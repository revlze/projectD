# Running series on a VPS

The runner only waits on the API, so a small server is enough: the test run (1824 episodes,
30 workers) took 34 minutes on 1 vCPU and 1 GB RAM with about 85 MB per process. The code has no
dependencies; the server needs git, python3 >= 3.11, curl and tmux, but no GitHub access.

Secrets stay out of the repository:

- `.env` in the repository root (git-ignored): `MISTRAL_API_KEY`.
- `~/.config/project-d/notify.env` (mode 600): `TG_TOKEN` of the control bot and `TG_CHAT`, the
  chat that receives notifications. Optional; without it no watcher is started.

Run from a clean tree on the commit you want to measure:

```
scripts/vps/deploy.sh ne_vps E2 E3 E4-H1 E4-delay          # test split (default --allow-test)
EXTRA_ARGS="" scripts/vps/deploy.sh ne_vps E1                # dev split
```

`deploy.sh` sends the commit as a git bundle, checks it out detached in `~/project-d`, copies the
secrets with mode 600 and starts tmux session `series`: window 0 runs `run_series.sh` (series one
after another, stop on any failure or audit issue, log in `~/series_progress.log`), window
`notify` runs `watch.sh` (events at once, a summary every 5 minutes, an alert if the run dies).

Fetch the results and check them:

```
ssh ne_vps bash -c "'cd ~/project-d/outputs && tar cf - <series dirs>'" | tar xf - -C outputs
```

then compare per-file `sha256` with `LC_ALL=C` sorting on both sides and load every episode
through `RunStore.load`. Afterwards remove the secrets: `scripts/vps/cleanup.sh ne_vps` or, to
remove everything, `scripts/vps/cleanup.sh ne_vps --all`.
