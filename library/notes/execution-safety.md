# Execution Safety

Target repository code includes installs, lifecycle scripts, hooks, tests, linters, type checkers, builds, generators, migrations, servers, browser applications, and commands copied from repository documentation.

Every target command runs inside an enforced execution sandbox with these properties:

- The user checkout is outside writable mounts.
- The validation copy has separate disposable Git administration and cannot mutate the user checkout's refs, config, hooks, index, or objects.
- Environment variables use an explicit allowlist. Host secrets, credential stores, SSH and signing agent sockets, cloud credentials, and service tokens are absent.
- The sandbox cannot reach host service sockets or cloud metadata endpoints.
- Network access is denied by default. A check that requires a remote dependency or service uses a named destination allowlist and disposable credentials with the smallest useful scope.
- Browser applications and test servers remain inside the same boundary. They use disposable local services or explicitly allowed test systems, never implicit staging or production endpoints.
- Filesystem writes remain inside disposable writable paths whose contents can be inspected before cleanup.
- The review record states which controls were enforced and which checks could not run.

A worktree, clone, container name, clean final status, or manual script inspection does not prove these properties. The harness must enforce them. When it cannot, the reviewer continues static, historical, and platform analysis without executing target code.

Before and after status comparison remains useful for detecting accidental drift. It is a secondary check, not proof that transient, ignored, metadata, or out-of-tree writes never occurred.
