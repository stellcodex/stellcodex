# PREFLIGHT REPORT

Generated At: 2026-03-05T13:47:19Z

## Workspace Checks
- /root/workspace exists: true
- /root/workspace/ops/orchestra exists: true

## uname
```
Linux ns1.localhost.com 5.4.0-216-generic #236-Ubuntu SMP Fri Apr 11 19:53:21 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
```

## lscpu
```
Architecture:                       x86_64
CPU op-mode(s):                     32-bit, 64-bit
Byte Order:                         Little Endian
Address sizes:                      40 bits physical, 48 bits virtual
CPU(s):                             2
On-line CPU(s) list:                0,1
Thread(s) per core:                 1
Core(s) per socket:                 2
Socket(s):                          1
NUMA node(s):                       1
Vendor ID:                          GenuineIntel
CPU family:                         15
Model:                              6
Model name:                         Common KVM processor
Stepping:                           1
CPU MHz:                            2199.998
BogoMIPS:                           4399.99
Hypervisor vendor:                  KVM
Virtualization type:                full
L1d cache:                          64 KiB
L1i cache:                          64 KiB
L2 cache:                           8 MiB
L3 cache:                           16 MiB
NUMA node0 CPU(s):                  0,1
Vulnerability Gather data sampling: Not affected
Vulnerability Itlb multihit:        KVM: Vulnerable
Vulnerability L1tf:                 Mitigation; PTE Inversion
Vulnerability Mds:                  Vulnerable: Clear CPU buffers attempted, no microcode; SMT Host state unknown
Vulnerability Meltdown:             Mitigation; PTI
Vulnerability Mmio stale data:      Unknown: No mitigations
Vulnerability Retbleed:             Not affected
Vulnerability Spec store bypass:    Vulnerable
Vulnerability Spectre v1:           Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:           Mitigation; Retpolines; STIBP disabled; RSB filling; PBRSB-eIBRS Not affected; BHI Retpoline
Vulnerability Srbds:                Not affected
Vulnerability Tsx async abort:      Not affected
Flags:                              fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx lm constant_tsc nopl xtopology cpuid tsc_known_freq pni cx16 x2apic hypervisor lahf_lm cpuid_fault pti
```

## free
```
              total        used        free      shared  buff/cache   available
Mem:          3.8Gi       2.8Gi       152Mi        11Mi       865Mi       740Mi
Swap:         2.9Gi       1.0Gi       1.8Gi
```

## df
```
Filesystem      Size  Used Avail Use% Mounted on
udev            1.9G     0  1.9G   0% /dev
tmpfs           392M  1.3M  391M   1% /run
/dev/vda5        56G   44G  8.9G  84% /
tmpfs           2.0G  4.0K  2.0G   1% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           2.0G     0  2.0G   0% /sys/fs/cgroup
/dev/vda1       456M   84M  338M  20% /boot
tmpfs           392M     0  392M   0% /run/user/0
overlay          56G   44G  8.9G  84% /var/lib/docker/overlay2/c7a6529ea272f71caaeb66706120341ea6214ba0e43662fe73cd09bc73aba53f/merged
overlay          56G   44G  8.9G  84% /var/lib/docker/overlay2/5f0fb9ec1782880d6d48298da723f959a080325ead585fde91978c1feb8198a2/merged
overlay          56G   44G  8.9G  84% /var/lib/docker/overlay2/94896a991c48dcbfe20c2d521cbe8888fd7458900583d96938ec9526591a3828/merged
shm              64M     0   64M   0% /var/lib/docker/containers/27995c2bdb05523761a6e2233c10c2374b95f3a87ef06f6d24bf78e79df57014/mounts/shm
shm              64M  1.1M   63M   2% /var/lib/docker/containers/1ade785f38be9e630fffbe5b5f8e719f1abb76fe9206d4317bc7e385e4abd487/mounts/shm
shm              64M     0   64M   0% /var/lib/docker/containers/ee7d89f8088f498b68ccb3b8bc3849bdca436a110610b444a5f200f28ba6eb90/mounts/shm
overlay          56G   44G  8.9G  84% /var/lib/docker/overlay2/c48eaef2c947f86ede2400a3756a3fdf3a6b38845a339477ced5aee5df4bf910/merged
overlay          56G   44G  8.9G  84% /var/lib/docker/overlay2/15690952a72aa7100d12335767fad9c8804a9dd4297586a52456f453cd242f31/merged
shm              64M     0   64M   0% /var/lib/docker/containers/e9f0f11aecbaf0b3c771550704a7f5650d8e66d537b63bcc7200e454a5434901/mounts/shm
shm              64M     0   64M   0% /var/lib/docker/containers/6cd381da9005a6f7a58c47b5afde6a15fb555b8637def787434f8d40c48cbc78/mounts/shm
overlay          56G   44G  8.9G  84% /var/lib/docker/overlay2/639d0adc80fd31f5c7507851f6092cc921e338b17685d350370241499f2de36f/merged
shm              64M     0   64M   0% /var/lib/docker/containers/7e02123f185d7d332ec1c0d14c86dad41068658692391ebc6d377d20aeecd861/mounts/shm
overlay          56G   44G  8.9G  84% /var/lib/docker/overlay2/d165327f918cf477e957cd30fa6d3742e238c7f17e6411626516f195ed4b24a6/merged
shm              64M     0   64M   0% /var/lib/docker/containers/cd828d1491ad931a3e29111650fcfc02dcbb8b0ec26f8b83dedefd1c0fdace3d/mounts/shm
overlay          56G   44G  8.9G  84% /var/lib/docker/overlay2/4b196842d3de2d0e0705fa45579bc856b39df11df2caf468f31c30ff8701208d/merged
shm              64M     0   64M   0% /var/lib/docker/containers/bf6434b66b393d8dd417bc656118ed85d789e19c1c9205d6e28c8f71666307a9/mounts/shm
```

## uptime
```
 16:47:18 up 6 days, 20:50,  2 users,  load average: 7.21, 6.13, 7.49
```

## docker_info
```
Client:
 Version:    26.1.3
 Context:    default
 Debug Mode: false

Server:
 Containers: 8
  Running: 8
  Paused: 0
  Stopped: 0
 Images: 63
 Server Version: 26.1.3
 Storage Driver: overlay2
  Backing Filesystem: extfs
  Supports d_type: true
  Using metacopy: false
  Native Overlay Diff: true
  userxattr: false
 Logging Driver: json-file
 Cgroup Driver: cgroupfs
 Cgroup Version: 1
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 Swarm: inactive
 Runtimes: io.containerd.runc.v2 runc
 Default Runtime: runc
 Init Binary: docker-init
 containerd version: 
 runc version: 
 init version: 
 Security Options:
  apparmor
  seccomp
   Profile: builtin
 Kernel Version: 5.4.0-216-generic
 Operating System: Ubuntu 20.04.6 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 2
 Total Memory: 3.828GiB
 Name: ns1.localhost.com
 ID: fbceeed0-85d4-4a67-9640-7f0100c123c1
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Username: stellcodex@gmail.com
 Experimental: false
 Insecure Registries:
  127.0.0.0/8
 Live Restore Enabled: false

WARNING: No swap limit support
```

## docker_ps
```
CONTAINER ID   IMAGE                                      COMMAND                  CREATED             STATUS                 PORTS                                       NAMES
bf6434b66b39   orchestra_orchestrator                     "uvicorn app:app --h…"   About an hour ago   Up About an hour       0.0.0.0:7010->7010/tcp, :::7010->7010/tcp   orchestra_orchestrator_1
cd828d1491ad   orchestra_litellm                          "litellm --config /a…"   About an hour ago   Up About an hour       0.0.0.0:4000->4000/tcp, :::4000->4000/tcp   orchestra_litellm_1
7e02123f185d   ollama/ollama:latest                       "/bin/ollama serve"      2 hours ago         Up 2 hours             11434/tcp                                   orchestra_ollama_1
ee7d89f8088f   redis:7                                    "docker-entrypoint.s…"   6 hours ago         Up 6 hours (healthy)   127.0.0.1:6379->6379/tcp                    stellcodex-redis
1ade785f38be   postgres:15                                "docker-entrypoint.s…"   6 hours ago         Up 6 hours (healthy)   127.0.0.1:5432->5432/tcp                    stellcodex-postgres
27995c2bdb05   minio/minio:RELEASE.2022-10-24T18-35-07Z   "/usr/bin/docker-ent…"   6 hours ago         Up 6 hours (healthy)   127.0.0.1:9000-9001->9000-9001/tcp          stellcodex-minio
6cd381da9005   deploy_backend                             "sh -lc '  DB_HOST=$…"   6 hours ago         Up 4 hours (healthy)   127.0.0.1:8000->8000/tcp                    stellcodex-backend
e9f0f11aecba   deploy_worker                              "sh -lc '  REDIS_HOS…"   6 hours ago         Up 6 hours                                                         stellcodex-worker
```

## dns
```
2606:4700::6812:1b78 example.com
2606:4700::6812:1a78 example.com
```

## curl_example
```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
HTTP/2 200 
date: Thu, 05 Mar 2026 13:47:19 GMT
content-type: text/html
cf-ray: 9d7992682923e430-IST
last-modified: Wed, 25 Feb 2026 07:22:28 GMT
allow: GET, HEAD
accept-ranges: bytes
age: 11421
cf-cache-status: HIT
server: cloudflare

```

## git_status_root
```
fatal: not a git repository (or any of the parent directories): .git
```

## git_status_orchestra
```
fatal: not a git repository (or any of the parent directories): .git
```

## orchestra_state
```
{"deferred_count":21,"last_routing":{"ts":"2026-03-05T13:21:37.912197Z","event":"orchestrate","task_preview":"startup smoke: validate orchestra routing and readiness","speed":"eco","readiness":"DEGRADED","routing":[{"role":"gemini","task_type":"plan","preferred":"startup_failfast","selected":"startup_failfast","shadow":null,"pinned":true,"decision":"pinned_or_strict_single_role","ranked":[{"model":"startup_failfast","score":0.5,"preferred":true,"order":0}]},{"role":"codex","task_type":"code","preferred":"codex_executor","selected":"codex_executor","pinned":true,"decision":"defer_and_degrade","reason":"pinned_model_in_cooldown"},{"role":"abacus","task_type":"analysis","preferred":"startup_failfast","selected":"startup_failfast","shadow":null,"pinned":true,"decision":"pinned_or_strict_single_role","ranked":[{"model":"startup_failfast","score":0.5,"preferred":true,"order":0}]},{"role":"claude","task_type":"review","preferred":"startup_failfast","selected":"startup_failfast","shadow":null,"pinned":true,"decision":"pinned_or_strict_single_role","ranked":[{"model":"claude_reviewer","score":0.94,"preferred":false,"order":1},{"model":"startup_failfast","score":0.5,"preferred":true,"order":0}]},{"role":"local_ops_check","task_type":"ops_check","preferred":null,"selected":null,"shadow":null,"pinned":false,"decision":"defer_and_degrade","reason":"no_available_model","ranked":[]},{"role":"local_doc","task_type":"doc","preferred":null,"selected":null,"shadow":null,"pinned":false,"decision":"defer_and_degrade","reason":"no_available_model","ranked":[]}],"results":[{"role":"gemini","task_type":"plan","model":"startup_failfast","status":"degraded_error","degraded":true,"deferred":false},{"role":"codex","task_type":"code","model":"codex_executor","status":"deferred_primary_cooldown","degraded":true,"deferred":true},{"role":"abacus","task_type":"analysis","model":"startup_failfast","status":"degraded_error","degraded":true,"deferred":false},{"role":"claude","task_type":"review","model":"startup_failfast","status":"degraded_error","degraded":true,"deferred":false},{"role":"local_ops_check","task_type":"ops_check","model":"local_fast","status":"deferred_no_available_model","degraded":true,"deferred":true},{"role":"local_doc","task_type":"doc","model":"local_fast","status":"deferred_no_available_model","degraded":true,"deferred":true}],"deferred_count":27}}```

