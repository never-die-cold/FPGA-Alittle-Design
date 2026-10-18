#ifndef COP_WORK_ORDER_H
#define COP_WORK_ORDER_H
#include <stdint.h>

enum cop_verdict { COP_CHECK_PASS=1, COP_CHECK_FAIL=2, COP_RECHECK=3 };
enum cop_reason {
    COP_REASON_TARGET_LIMIT=1, COP_REASON_INVALID=2,
    COP_REASON_LOW_CONF=4, COP_REASON_CLASS=8, COP_REASON_CONFIG=16
};
struct cop_order { uint8_t expected[3]; uint8_t policy_max; };
struct cop_target { uint8_t class_id; uint8_t valid; uint8_t low_conf; uint8_t error; };
struct cop_judgement { uint8_t actual[3]; uint8_t verdict; uint8_t reasons; };

static inline struct cop_judgement cop_judge(
    const struct cop_target *targets, uint8_t target_count, struct cop_order order)
{
    struct cop_judgement out={{0,0,0},COP_RECHECK,0};
    uint8_t index,total=(uint8_t)(order.expected[0]+order.expected[1]+order.expected[2]);
    if(order.policy_max==0 || order.policy_max>10 || total==0 || total>order.policy_max) {
        out.reasons=COP_REASON_CONFIG; return out;
    }
    if(target_count>10) { out.reasons=COP_REASON_TARGET_LIMIT; return out; }
    for(index=0;index<target_count;index++) {
        if(!targets[index].valid || targets[index].error) out.reasons|=COP_REASON_INVALID;
        if(targets[index].low_conf) out.reasons|=COP_REASON_LOW_CONF;
        if(targets[index].class_id>2) out.reasons|=COP_REASON_CLASS;
        else out.actual[targets[index].class_id]++;
    }
    if(out.reasons) out.verdict=COP_RECHECK;
    else if(out.actual[0]==order.expected[0] && out.actual[1]==order.expected[1] &&
            out.actual[2]==order.expected[2]) out.verdict=COP_CHECK_PASS;
    else out.verdict=COP_CHECK_FAIL;
    return out;
}
#endif
