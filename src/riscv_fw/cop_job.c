#include <stdint.h>
#include "cop_work_order.h"

extern volatile unsigned int tohost;
#define COP ((volatile uint32_t *)0x80010000u)
enum {
    REG_CTRL=0x00c/4, REG_STATUS=0x010/4, REG_ROI_COUNT=0x02c/4,
    REG_WORK_ORDER=0x034/4, REG_RESULT_INDEX=0x06c/4,
    REG_RESULT_META=0x070/4, REG_RESULT_SEQ=0x07c/4,
    REG_FW_COUNTS=0x088/4, REG_FW_DECISION=0x08c/4
};
enum { STATUS_DONE=4, STATUS_ERROR=8, STATUS_TIMEOUT=16, STATUS_PENDING=1024 };

static void cop_write(unsigned int reg, uint32_t value)
{
    while(COP[REG_STATUS]&STATUS_PENDING) { }
    COP[reg]=value;
    while(COP[REG_STATUS]&STATUS_PENDING) { }
}

int main(void)
{
    struct cop_target targets[16]; struct cop_judgement judged;
    struct cop_order order; uint32_t word,status=0,seq=0,decision;
    unsigned int index,count=COP[REG_ROI_COUNT]&31u;
    word=COP[REG_WORK_ORDER];
    order.expected[0]=(uint8_t)word; order.expected[1]=(uint8_t)(word>>8);
    order.expected[2]=(uint8_t)(word>>16); order.policy_max=(uint8_t)(word>>24);
    if(count<=10u) {
        cop_write(REG_CTRL,24u); cop_write(REG_CTRL,1u);
        while(!(status&(STATUS_DONE|STATUS_ERROR|STATUS_TIMEOUT))) status=COP[REG_STATUS];
    }
    if((status&STATUS_DONE) || count>10u) {
        for(index=0;index<count && index<16u;index++) {
            cop_write(REG_RESULT_INDEX,index); word=COP[REG_RESULT_META];
            targets[index].class_id=(uint8_t)(word>>16);
            targets[index].valid=(uint8_t)((word>>24)&1u);
            targets[index].low_conf=(uint8_t)((word>>25)&1u);
            targets[index].error=(uint8_t)((word>>26)&1u);
        }
        judged=cop_judge(targets,(uint8_t)count,order); seq=COP[REG_RESULT_SEQ];
    } else {
        judged.actual[0]=0; judged.actual[1]=0; judged.actual[2]=0;
        judged.verdict=COP_RECHECK; judged.reasons=COP_REASON_INVALID;
    }
    word=(uint32_t)judged.actual[0]|((uint32_t)judged.actual[1]<<8)|
         ((uint32_t)judged.actual[2]<<16);
    decision=(seq<<16)|((uint32_t)judged.reasons<<8)|judged.verdict;
    cop_write(REG_FW_COUNTS,word); cop_write(REG_FW_DECISION,decision);
    tohost=0x4a303400u|judged.verdict;
    return 0;
}
