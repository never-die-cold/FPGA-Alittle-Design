#include <stdint.h>
#include "cop_work_order.h"

extern volatile unsigned int tohost;
#define COP ((volatile uint32_t *)0x80010000u)
enum {
    REG_CTRL=0x00c/4, REG_STATUS=0x010/4, REG_CFG_APPLIED=0x020/4,
    REG_ROI_COUNT=0x02c/4,
    REG_WORK_ORDER=0x034/4, REG_RESULT_INDEX=0x06c/4,
    REG_RESULT_META=0x070/4, REG_RESULT_SEQ=0x07c/4, REG_DMA_BYTES=0x084/4,
    REG_FW_COUNTS=0x088/4, REG_FW_DECISION=0x08c/4
};
enum {
    STATUS_BUSY=2, STATUS_DONE=4, STATUS_ERROR=8, STATUS_TIMEOUT=16,
    STATUS_CFG_VALID=32, STATUS_MODEL_VALID=64, STATUS_RESULT_VALID=128,
    STATUS_DMA_BUSY=256, STATUS_PENDING=1024, STATUS_ACCEPTED=2048, STATUS_UNCONSUMED=4096
};
#define COP_POLL_LIMIT 1000000u

static int cop_write(unsigned int reg, uint32_t value)
{
    unsigned int guard=0;
    while(COP[REG_STATUS]&STATUS_PENDING) {
        if(++guard>COP_POLL_LIMIT) return -1;
    }
    COP[reg]=value;
    guard=0;
    while(COP[REG_STATUS]&STATUS_PENDING) {
        if(++guard>COP_POLL_LIMIT) return -1;
    }
    return 0;
}

static int run_job(void)
{
    struct cop_target targets[16]; struct cop_judgement judged;
    struct cop_order order; uint32_t word,status=0,seq=0,decision,seq_before,seq_after;
    unsigned int index,guard,count=0,cfg_applied;
    int ok=1;

    judged.actual[0]=0; judged.actual[1]=0; judged.actual[2]=0;
    judged.verdict=COP_RECHECK; judged.reasons=COP_REASON_INVALID;
    /* C03 §8 要求“有效空场景 → CHECK_FAIL（actual 三零）”，但 v0 没有“本帧有效且零目标”的表达：
       ROI_COUNT 只接受 1–16，0 分不清“未配置/无视频”和“有效空帧”。冻结前一律 RECHECK+CONFIG，
       不得把 0 当有效空帧（OPEN-11）。 */
    guard=0;
    for(;;) {
        status=COP[REG_STATUS]; count=COP[REG_ROI_COUNT]&31u;
        cfg_applied=COP[REG_CFG_APPLIED];
        if(status&(STATUS_BUSY|STATUS_UNCONSUMED)) {
            judged.reasons=COP_REASON_CONFIG; goto finish;
        }
        if(count>16u) { judged.reasons=COP_REASON_CONFIG; goto finish; }
        /* CFG_VALID proves CFG_APPLIED==CFG_SEQ. DMA_BYTES distinguishes the completed ROI load
           from the preceding 36,032-byte model transfer without adding a new register. */
        if(cfg_applied!=0u && (status&STATUS_CFG_VALID) && (status&STATUS_MODEL_VALID) &&
           !(status&STATUS_DMA_BUSY) && count!=0u && COP[REG_DMA_BYTES]==count*4096u) break;
        if(++guard>COP_POLL_LIMIT) { judged.reasons=COP_REASON_CONFIG; goto finish; }
    }
    word=COP[REG_WORK_ORDER];
    order.expected[0]=(uint8_t)word; order.expected[1]=(uint8_t)(word>>8);
    order.expected[2]=(uint8_t)(word>>16); order.policy_max=(uint8_t)(word>>24);
    if(count>10u) {
        judged.reasons=COP_REASON_TARGET_LIMIT; goto finish;
    }
    seq_before=COP[REG_RESULT_SEQ];
    if(cop_write(REG_CTRL,1u)!=0) {
        judged.reasons=COP_REASON_CONFIG; goto finish;
    }
    status=COP[REG_STATUS]; guard=0;
    while(!(status&STATUS_ACCEPTED)) {
        if(++guard>COP_POLL_LIMIT) { judged.reasons=COP_REASON_INVALID; goto finish; }
        status=COP[REG_STATUS];
    }
    status=COP[REG_STATUS]; guard=0;
    while(!(status&(STATUS_DONE|STATUS_ERROR|STATUS_TIMEOUT))) {
        if(++guard>COP_POLL_LIMIT) { judged.reasons=COP_REASON_INVALID; goto finish; }
        status=COP[REG_STATUS];
    }
    if(!(status&STATUS_DONE) || (status&(STATUS_ERROR|STATUS_TIMEOUT)) ||
       !(status&STATUS_RESULT_VALID)) {
        judged.reasons=COP_REASON_INVALID; goto finish;
    }
    seq=COP[REG_RESULT_SEQ];
    if(seq!=seq_before+1u) { judged.reasons=COP_REASON_INVALID; goto finish; }
    for(index=0;index<count;index++) {
        if(cop_write(REG_RESULT_INDEX,index)!=0) { ok=0; break; }
        word=COP[REG_RESULT_META];
        targets[index].class_id=(uint8_t)(word>>16);
        targets[index].valid=(uint8_t)((word>>24)&1u);
        targets[index].low_conf=(uint8_t)((word>>25)&1u);
        targets[index].error=(uint8_t)((word>>26)&1u);
    }
    seq_after=COP[REG_RESULT_SEQ];
    status=COP[REG_STATUS];
    if(!ok || seq!=seq_after || !(status&STATUS_RESULT_VALID)) {
        judged.reasons=COP_REASON_INVALID; goto finish;
    }
    judged=cop_judge(targets,(uint8_t)count,order);

finish:
    word=(uint32_t)judged.actual[0]|((uint32_t)judged.actual[1]<<8)|
         ((uint32_t)judged.actual[2]<<16);
    decision=(seq<<16)|((uint32_t)judged.reasons<<8)|judged.verdict;
    if(cop_write(REG_FW_COUNTS,word)!=0 || cop_write(REG_FW_DECISION,decision)!=0)
        judged.verdict=COP_RECHECK;
    tohost=0x4a303400u|judged.verdict;
    return 0;
}

int main(void)
{
    uint32_t last_config=0;
    for(;;) {
        uint32_t status=COP[REG_STATUS], config=COP[REG_CFG_APPLIED];
        uint32_t count=COP[REG_ROI_COUNT]&31u;
        /* A committed configuration is the job receipt. PS persists and consumes
           its terminal before committing a new sequence; idle has no deadline. */
        if(config==0u || config==last_config || count==0u ||
           (status&(STATUS_BUSY|STATUS_UNCONSUMED|STATUS_DMA_BUSY)) ||
           !(status&STATUS_CFG_VALID) || !(status&STATUS_MODEL_VALID) ||
           COP[REG_DMA_BYTES]!=count*4096u) continue;
        last_config=config;
        run_job();
    }
}
