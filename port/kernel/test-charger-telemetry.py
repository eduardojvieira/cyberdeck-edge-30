#!/usr/bin/env python3
"""Compile real charger read/ACK functions with a deterministic host transport.

No phone, Docker, networking or power writes. --baseline demonstrates the bug.
This checks response ownership, not kernel scheduling or electrical behavior.
"""
from pathlib import Path
import argparse
import resource
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
REL = Path('motorola/drivers/power/qti_glink_charger/qti_glink_charger.c')
REF = ROOT / 'reference/repos/eqs-development/android_kernel_motorola_sm8475-modules'
PATCH = ROOT / 'port/kernel/patches/0002-qti-charger-read-only-telemetry.patch'


def function(source, start):
    begin = source.index(start)
    end = source.index('\n}', begin) + 2
    return source[begin:end]


PRELUDE = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
typedef uint32_t u32;
typedef unsigned char u8;
typedef int32_t s32;
typedef int atomic_t;
typedef int spinlock_t;
struct mutex { int locked; };
struct completion { int done; };
struct pmic_glink_hdr { u32 owner, type, opcode; };
struct oem_read_buf_req_msg { struct pmic_glink_hdr hdr; u32 oem_property_id, data_size; };
struct oem_read_buf_resp_msg { struct pmic_glink_hdr hdr; u32 oem_property_id, buf[16], data_size; };
struct qti_charger {
    void *client;
    atomic_t state, rx_valid;
    struct mutex read_lock;
    struct completion read_ack;
    struct oem_read_buf_resp_msg rx_buf;
    spinlock_t rx_lock;
    u32 rx_property, switched_nums;
    bool adc_read_failed;
};
#define PMIC_GLINK_STATE_DOWN 0
#define PMIC_GLINK_STATE_UP 1
#define MSG_OWNER_OEM 32782
#define MSG_TYPE_REQ_RESP 1
#define OEM_READ_BUF_REQ 0x10000
#define OEM_PROPERTY_DATA_SIZE 16
#define OEM_WAIT_TIME_MS 5000
#define PAGE_SIZE 4096
#define BUILD_BUG_ON(x) _Static_assert(!(x), "wire size changed")
#define mmi_err(...) ((void)0)
#define mmi_dbg(...) ((void)0)
#define atomic_read(p) (*(p))
#define atomic_set(p,v) (*(p)=(v))
#define spin_lock_irqsave(p,f) do { (f)=0; assert(!*(p)); *(p)=1; } while (0)
#define spin_unlock_irqrestore(p,f) do { (void)(f); assert(*(p)); *(p)=0; } while (0)
static void mutex_lock(struct mutex *m) { assert(!m->locked); m->locked=1; }
static void mutex_unlock(struct mutex *m) { assert(m->locked); m->locked=0; }
static int mutex_trylock(struct mutex *m) { if (m->locked) return 0; m->locked=1; return 1; }
static void reinit_completion(struct completion *c) { c->done=0; }
static void complete(struct completion *c) { c->done++; }
static int wait_for_completion_timeout(struct completion *c, int t) { assert(t==5000); return c->done; }
static int msecs_to_jiffies(int t) { return t; }
static int mode, sends;
static int pmic_glink_write(void *, void *, size_t);
struct device { struct qti_charger *chg; };
struct device_attribute { int unused; };
#define dev_get_drvdata(dev) ((dev)->chg)
#define scnprintf snprintf
'''

TRANSPORT = r'''
static int pmic_glink_write(void *client, void *data, size_t size)
{
    struct qti_charger *c = client;
    struct oem_read_buf_req_msg *req = data;
    struct oem_read_buf_resp_msg rsp = {0};
    sends++;
    assert(size==sizeof(*req) && req->hdr.opcode==OEM_READ_BUF_REQ);
    assert(req->hdr.owner==MSG_OWNER_OEM && req->hdr.type==MSG_TYPE_REQ_RESP);
    assert(req->oem_property_id==OEM_PROP_MASTER_SWITCHEDCAP_INFO ||
           req->oem_property_id==OEM_PROP_SLAVE_SWITCHEDCAP_INFO ||
           req->oem_property_id==OEM_PROP_BATT_INFO ||
           req->oem_property_id==OEM_PROP_CHG_INFO ||
           req->oem_property_id==OEM_PROP_LPD_INFO ||
           req->oem_property_id==OEM_PROP_WLS_DUMP_INFO);
    if (mode==3) return 0; /* response timeout */
    if (mode==6) return -EIO;
    rsp.hdr=req->hdr;
    rsp.oem_property_id=(mode==12 ? 0 : req->oem_property_id);
    rsp.data_size=req->data_size;
    for (unsigned i=0; i<16; i++) rsp.buf[i]=5200;
    if (req->data_size==40) rsp.buf[0]=0x00000101;
    if (mode==9) rsp.buf[0]=0xff; /* invalid wire bool */
    if (mode==1 || mode==7) {
        rsp.oem_property_id=OEM_PROP_LPD_INFO;
        handle_oem_read_ack(c, &rsp, sizeof(rsp));
        if (mode==1) return 0;
        rsp.oem_property_id=req->oem_property_id;
    }
    if (mode==2) rsp.data_size=65;
    if (mode==14) { rsp.oem_property_id=0; rsp.data_size=0; } /* observed no-hub ADC */
    if (mode==4) { handle_oem_read_ack(c, &rsp, 12); return 0; }
    if (mode==8) c->state=PMIC_GLINK_STATE_DOWN;
    if (mode==11) rsp.hdr.owner=0;
    handle_oem_read_ack(c, &rsp, sizeof(rsp));
    if (mode==5) { rsp.buf[0]=9999; handle_oem_read_ack(c, &rsp, sizeof(rsp)); }
    return 0;
}
static void init(struct qti_charger *c)
{
    memset(c, 0, sizeof(*c));
    c->client=c; c->state=PMIC_GLINK_STATE_UP;
    c->rx_property=OEM_PROP_MAX; c->switched_nums=1;
}
int main(int argc, char **argv)
{
    struct qti_charger c;
    u32 output=0xdeadbeef;
    assert(argc==2);
    mode=atoi(argv[1]);
    init(&c);
    if (mode==12) {
        /* Observed RETAR firmware ACKs: the property field remains zero. */
        u32 data[15];
        assert(qti_charger_read(&c, OEM_PROP_BATT_INFO, data, 40)==0);
        assert(qti_charger_read(&c, OEM_PROP_CHG_INFO, data, 24)==0);
        assert(qti_charger_read(&c, OEM_PROP_LPD_INFO, data, 16)==0);
        assert(qti_charger_read(&c, OEM_PROP_WLS_DUMP_INFO, data, 60)==0);
        assert(qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, data, 40)==0);
        return 0;
    }
    if (mode==13) {
        /* A late normal battery reply also aliases the 40-byte ADC reply. */
        u32 data[10];
        mode=3;
        assert(qti_charger_read(&c, OEM_PROP_BATT_INFO, data, sizeof(data))==-ETIMEDOUT);
        int old_sends=sends;
        mode=0;
        assert(qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, data, sizeof(data))==-EPIPE);
        assert(sends==old_sends);
        assert(qti_charger_read(&c, OEM_PROP_BATT_INFO, data, sizeof(data))==0);
        return 0;
    }
#ifdef TEST_SNAPSHOT
    if (mode==10) {
        char buf[PAGE_SIZE]; struct device dev={&c};
        mode=0;
        assert(switchedcap_snapshot_show(&dev, NULL, buf)>0);
        assert(strstr(buf, "raw=1 index=0 chg_en=1") && strstr(buf, "vusb_mv=5200"));
        c.switched_nums=2;
        assert(switchedcap_snapshot_show(&dev, NULL, buf)>0);
        assert(strstr(buf, "index=1"));
        c.switched_nums=3; int old_sends=sends;
        assert(switchedcap_snapshot_show(&dev, NULL, buf)==-EOPNOTSUPP && sends==old_sends);
        c.switched_nums=1; mode=9;
        assert(switchedcap_snapshot_show(&dev, NULL, buf)==-ENODATA);
        mode=3;
        assert(switchedcap_snapshot_show(&dev, NULL, buf)==-ETIMEDOUT);
        return 0;
    }
#endif
    int rc=qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, &output, sizeof(output));
    if (mode==0 || mode==5 || mode==7) {
        assert(rc==0 && output==5200);
        assert(qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, &output, sizeof(output))==0);
    } else {
        assert(rc<0 && output==0xdeadbeef);
        if (mode==14) assert(rc==-ENODATA); /* empty reply is not a zero reading */
        /* Same-property late replies must not make an ADC retry look fresh. */
        mode=0; c.state=PMIC_GLINK_STATE_UP;
        int old_sends=sends;
        assert(qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, &output, sizeof(output))<0);
        assert(sends==old_sends && output==0xdeadbeef);
        /* Diagnostic failure must not disable normal charger telemetry. */
        assert(qti_charger_read(&c, OEM_PROP_BATT_INFO, &output, sizeof(output))==0);
    }
    init(&c); c.read_lock.locked=1; int old_sends=sends;
    assert(qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, &output, sizeof(output))==-EBUSY);
    assert(sends==old_sends && !c.adc_read_failed);
    c.read_lock.locked=0;
    assert(qti_charger_read(&c, OEM_PROP_MAX, &output, sizeof(output))==-EINVAL);
    assert(qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, NULL, sizeof(output))==-EINVAL);
    assert(qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, &output, 0)==-EINVAL);
    assert(qti_charger_read(&c, OEM_PROP_MASTER_SWITCHEDCAP_INFO, &output, 65)==-EINVAL);
    assert(sends==old_sends);
    return 0;
}
'''

args = argparse.ArgumentParser(description=__doc__)
args.add_argument('--baseline', action='store_true')
options = args.parse_args()
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
assert subprocess.check_output(['git', '-C', str(REF), 'rev-parse', 'HEAD'], text=True).strip() == '9f8d247d457622c08ff547e5498e6fa453e876ed'
subprocess.run(['git', '-C', str(REF), 'diff', '--quiet', 'HEAD', '--', str(REL), str(REL.with_suffix('.h'))], check=True)
with tempfile.TemporaryDirectory(prefix='eqs-charger-test-') as temporary:
    stage = Path(temporary)
    path = stage / REL
    path.parent.mkdir(parents=True)
    shutil.copy2(REF / REL, path)
    if not options.baseline:
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', str(stage), '-i', str(PATCH)], check=True)
    source = path.read_text()
    header = (REF / REL.with_suffix('.h')).read_text()
    enum_start = header.index('enum {') if 'enum {' in header else header.index('enum oem_property')
    enums = header[enum_start:header.index('\n};', enum_start)+3]
    code = PRELUDE + enums + '\n' + function(source, 'static int handle_oem_read_ack(')
    code += '\n' + function(source, 'static int qti_charger_read(')
    if not options.baseline:
        start = header.index('struct switched_dev_info\n')
        code += '\n' + header[start:header.index('\n};', start)+3]
        code += '\n' + function(source, 'static ssize_t switchedcap_snapshot_show(')
        code += '\n#define TEST_SNAPSHOT\n'
        assert '__ATTR(switchedcap_snapshot, 0400, switchedcap_snapshot_show, NULL)' in source
        assert 'device_remove_file(chg->dev, &dev_attr_switchedcap_snapshot)' in source
        assert 'spin_lock_init(&chg->rx_lock)' in source
        assert 'qti_charger_write' not in function(source, 'static ssize_t switchedcap_snapshot_show(')
    code += '\n' + TRANSPORT
    c_file = stage / 'test.c'
    c_file.write_text(code)
    executable = stage / 'test'
    subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
                    '-Wno-unused-variable', '-Wno-unused-parameter', '-Wno-missing-field-initializers',
                    '-fsanitize=undefined', '-fno-sanitize-recover=all',
                    '-o', str(executable), str(c_file)], check=True)
    failed = []
    cases = {0: 'valid repeat', 1: 'wrong property', 2: 'invalid payload size',
             3: 'timeout/retry latch', 4: 'truncated response', 5: 'duplicate response',
             6: 'send failure', 7: 'mismatch then valid', 8: 'link loss',
             11: 'wrong response owner', 12: 'observed firmware zero property ACK',
             13: 'normal timeout disables ambiguous ADC, not charger',
             14: 'observed empty ADC reply is no data, never a measurement'}
    if not options.baseline:
        cases[10] = 'raw snapshot, count bounds, invalid bool, error propagation'
    for case, name in cases.items():
        result = subprocess.run([str(executable), str(case)], capture_output=True, text=True, timeout=10)
        print(f'{name}: {"PASS" if result.returncode == 0 else "FAIL"}')
        if result.returncode:
            failed.append(case)
            print(result.stderr.strip())
    assert not failed, f'failed response cases: {failed}'
    print('PASS: host response-boundary checks; no target/electrical validation')
