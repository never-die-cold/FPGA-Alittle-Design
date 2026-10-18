#include <assert.h>
#include <stdio.h>
#include "cop_work_order.h"
int main(void)
{
    struct cop_order order={{1,1,1},10};
    struct cop_target targets[11]={{0,1,0,0},{1,1,0,0},{2,1,0,0}};
    struct cop_judgement got=cop_judge(targets,3,order);
    assert(got.verdict==COP_CHECK_PASS && got.actual[0]==1 && got.actual[1]==1 && got.actual[2]==1);
    got=cop_judge(targets,2,order); assert(got.verdict==COP_CHECK_FAIL && got.actual[2]==0);
    targets[0].low_conf=1; got=cop_judge(targets,3,order);
    assert(got.verdict==COP_RECHECK && (got.reasons&COP_REASON_LOW_CONF) && got.actual[0]==1);
    targets[0].low_conf=0; got=cop_judge(targets,11,order);
    assert(got.verdict==COP_RECHECK && got.reasons==COP_REASON_TARGET_LIMIT);
    order.policy_max=16; got=cop_judge(targets,3,order);
    assert(got.verdict==COP_RECHECK && got.reasons==COP_REASON_CONFIG);
    puts("PASS: cop work-order PASS/FAIL/RECHECK, low-confidence and 10/16 policy");
    return 0;
}
