---
title: "scp vs rsync: Copying Files Between Machines"
date: 2026-10-14T10:00:00+05:30
draft: false
tags: ["linux-utilities"]
summary: "The scp and rsync commands I actually use, what each tool does under the hood, a point-by-point comparison, and how to run rsync in parallel when one stream isn't fast enough."
references:
  - id: so-scp-rsync
    text: 'Stack Overflow. "How does scp differ from rsync?" 2013.'
    url: https://stackoverflow.com/questions/20244585/how-does-scp-differ-from-rsync
  - id: rsync-paper
    text: 'Andrew Tridgell, Paul Mackerras. "The rsync algorithm." Technical Report TR-CS-96-05, Australian National University, 1996.'
    url: https://rsync.samba.org/tech_report/
  - id: openssh80
    text: 'OpenSSH 8.0 release notes. 2019.'
    url: https://www.openssh.com/txt/release-8.0
  - id: openssh90
    text: 'OpenSSH 9.0 release notes. 2022.'
    url: https://www.openssh.com/txt/release-9.0
---

`scp` and `rsync` both copy files from one machine to another over SSH, and for a single
command they often look interchangeable:

```bash
scp   -r ./site user@server:/var/www/
rsync -a ./site user@server:/var/www/
```

So why does anyone bother with two tools? This is a classic Stack Overflow question{{< cite "so-scp-rsync" >}}:
a tutorial uses `scp` to pull a directory from a server, then switches to `rsync` to push it
back, and the asker wants to know why.

The one-line answer: **`scp` copies, `rsync` synchronises.** `scp` streams every byte of every
file, every time. `rsync` first works out what the other side already has, and sends only what
is missing or different. Everything else follows from that.

This post first collects the commands I actually use for each tool, then goes under the hood,
compares them point by point, and ends with running transfers in parallel when one stream
isn't fast enough.

## scp: secure copy

`scp` is the "cp over SSH" tool. It ships with OpenSSH, so it exists anywhere you can `ssh`
into. It authenticates the same way `ssh` does (keys, agent, `~/.ssh/config` aliases) and
everything it sends is encrypted.

The syntax is just `cp` with `host:` in front of remote paths:

```bash
# local -> remote
scp notes.txt user@server:/tmp/
scp notes.txt server:                    # "server:" with no path means your home directory

# remote -> local
scp user@server:/var/log/syslog .

# whole directories need -r
scp -r ./project user@server:~/

# remote -> remote (by default the data flows through your machine)
scp alpha:/data/model.pt beta:/data/
```

The flags worth remembering:

| Flag | What it does |
|------|--------------|
| `-r` | Recursive, for directories |
| `-p` | Preserve modification times and permissions |
| `-P 2222` | SSH port (capital P; `ssh` uses lowercase `-p`, a classic trip-up) |
| `-i ~/.ssh/key` | Use a specific private key |
| `-J bastion` | Hop through a jump host |
| `-C` | Compress in transit |
| `-l 8000` | Limit bandwidth, in **Kbit/s** |
| `-o Option=value` | Pass any `ssh` option through |

Good to know: modern `scp` is no longer the protocol it was named after. The original SCP
protocol worked by running a shell on the remote side, which expanded wildcards and
interpreted special characters in remote file names. That is why remote paths with spaces
used to need double escaping (`scp 'host:My\ File.txt' .`), and why a hostile server could
send back files you never asked for.[^cve] The OpenSSH developers called the protocol
"outdated, inflexible and not readily fixed" and recommended sftp and rsync
instead{{< cite "openssh80" >}}. Since OpenSSH 9.0 (2022), the `scp` command talks the SFTP
protocol by default, and `-O` brings back the legacy protocol for old servers{{< cite "openssh90" >}}.
The command line stayed the same, so most people never noticed.

[^cve]: CVE-2019-6111: the legacy client didn't check that the file names the server sent matched the ones requested. OpenSSH 8.0 added that check.

## rsync: remote sync

`rsync` copies files locally or between machines, but its job is to make the destination look
like the source while moving as little data as possible. Over the network it uses SSH by
default (`host:path`, one colon), so it is just as encrypted as `scp`. It needs the `rsync`
binary installed on **both** ends, because a copy of `rsync` runs on the remote side and the two
talk to each other.

The commands I use most:

```bash
# the default: archive mode, verbose, human-readable sizes
rsync -avh ./project/ user@server:~/project/

# pull from remote
rsync -avh user@server:/var/log/nginx/ ./nginx-logs/

# big files or flaky links: show progress, keep partial files so a re-run resumes
rsync -avhP bigdata.tar user@server:/data/

# overall progress for a large tree instead of one line per file
rsync -ah --info=progress2 ./dataset/ server:/data/dataset/

# dry run first: show what WOULD change, touch nothing
rsync -avhn --delete ./site/ server:/var/www/site/

# exact mirror: also delete files at the destination that no longer exist in the source
rsync -avh --delete ./site/ server:/var/www/site/

# skip things
rsync -avh --exclude '.git/' --exclude '*.pyc' --exclude 'node_modules/' ./repo/ server:~/repo/

# non-standard SSH port, key or jump host: pass a custom ssh command with -e
rsync -avh -e "ssh -p 2222 -i ~/.ssh/deploy_key" ./build/ server:/srv/app/
rsync -avh -e "ssh -J bastion" ./build/ internal-host:/srv/app/

# cap bandwidth (KiB/s here, unlike scp's Kbit/s)
rsync -avh --bwlimit=5000 ./backup/ server:/backups/

# a local copy works too, and beats cp -r when re-run
rsync -ah /mnt/old-disk/ /mnt/new-disk/
```

What the common flags mean (two from the commands above, `--exclude`[^exclude] and
`-e`,[^rsh] get side notes):

[^exclude]: `--exclude 'node_modules/'`: a trailing `/` matches only directories, a pattern without a `/` matches that name at any depth. Quote patterns so your shell doesn't expand them first.
[^rsh]: `-e` (long form `--rsh`) sets the command rsync uses to reach the remote. Anything you'd type after `ssh` goes inside the quotes.

| Flag | What it does |
|------|--------------|
| `-a` | Archive: recursive, and preserve symlinks, permissions, times, group, owner and device files. Equal to `-rlptgoD` |
| `-v` / `-h` | Verbose / human-readable numbers |
| `-z` | Compress in transit. Helps for text on slow links; wasted CPU for already-compressed data or a fast LAN |
| `-P` | `--partial --progress`: keep half-sent files and show progress |
| `-n` | `--dry-run` |
| `--delete` | Remove destination files missing from the source |
| `-H`, `-A`, `-X` | Preserve hard links, ACLs, extended attributes. **Not** included in `-a` |
| `-c` | Compare files by checksum instead of size and modification time (slow, reads everything) |
| `-i` | Itemise changes: print *why* each file was transferred |

### The trailing slash

The one rsync rule that bites everyone: a trailing slash on the **source** changes what gets
copied.

```bash
rsync -a src  dest/    # creates dest/src/...   (copies the directory itself)
rsync -a src/ dest/    # creates dest/...       (copies the directory's contents)
```

Think of `src/` as "the contents of src". A slash on the destination doesn't matter. `scp`
doesn't have this distinction, which is one reason the two commands at the top of this post
are not quite equivalent.

## How rsync decides what to send

Plain `scp` has no logic to describe: open the file, stream the bytes, repeat. `rsync` does
three extra things, and they explain both why it's faster on re-runs and why it's slightly
slower to start.

**1. The quick check.** For every file, rsync compares size and modification time between the
two sides. If both match, the file is skipped without reading its contents. This is why `-a`
(which includes `-t`, preserve times) matters so much: the Stack Overflow example used
`rsync -r`, which does *not* preserve times. On the next run every destination file has a
different modification time from its source, so rsync has to open and checksum every file
again. Nothing gets resent needlessly, but every file gets read on both sides. Use `-a`.

**2. The delta transfer.** When a file did change and an older version exists at the
destination, rsync sends only the parts that differ. The trick, from Tridgell and Mackerras'
1996 paper{{< cite "rsync-paper" >}}, is to find the differences without either machine
having both files:

```mermaid
sequenceDiagram
  participant S as Sender (has new file A)
  participant R as Receiver (has old file B)
  R->>S: Split B into fixed blocks; send a weak + strong checksum per block
  Note over S: Slide a window over A one byte at a time,<br/>look up each window's weak checksum
  S->>R: Matching blocks as "copy block #i"; everything else as literal bytes
  Note over R: Rebuild A into a temp file from old blocks + literals,<br/>verify a whole-file checksum, rename over B
```

The key is the *weak* checksum: a rolling checksum that can be updated in constant time as the
window slides by one byte. For a window $X_k \dots X_l$ (with $M = 2^{16}$):

$$
a(k,l) = \Big(\sum_{i=k}^{l} X_i\Big) \bmod M, \qquad
b(k,l) = \Big(\sum_{i=k}^{l} (l-i+1)\,X_i\Big) \bmod M
$$

and sliding the window one byte to the right only needs the byte leaving and the byte entering:

$$
\begin{aligned}
a(k+1,l+1) &= \big(a(k,l) - X_k + X_{l+1}\big) \bmod M \\
b(k+1,l+1) &= \big(b(k,l) - (l-k+1)\,X_k + a(k+1,l+1)\big) \bmod M
\end{aligned}
$$

So the sender can check *every* byte offset of A against B's blocks in one linear pass. That
is what lets rsync notice that you inserted a line near the top of a file: everything after
the insertion still matches, just shifted. The weak checksum produces false matches now and
then, so a candidate block is confirmed with a strong hash (MD4 in the paper; current rsync
versions negotiate MD5 or xxHash).

Two consequences worth knowing:

- The delta step only helps when an old version of the file **already exists** at the
  destination. For a first-time copy rsync has nothing to diff against and sends everything,
  just like `scp`.
- For local copies (disk to disk), rsync turns delta transfer off (`--whole-file`), since
  reading both files to save disk writes isn't worth it.

**3. Atomic replace and verification.** rsync writes each file to a temporary name and renames
it over the old one at the end, so a process reading the file never sees it half-written.
After reconstructing a file it compares a whole-file checksum against the sender's, and
retries the file if they disagree.

## scp vs rsync, point by point

| | scp | rsync |
|---|-----|-------|
| Transfer model | Copies every byte, every time | Skips unchanged files, sends only changed blocks |
| Re-running the same command | Full copy again | Near-instant if nothing changed |
| Resuming an interrupted transfer | No, starts over | Yes, with `-P` |
| Needs on the remote | Just `sshd` | `rsync` installed too |
| Encryption | Always SSH | SSH by default (`host:`); the rsync daemon (`host::`, `rsync://`) is unencrypted |
| Deleting extra files at the destination | No | `--delete` |
| Include/exclude filters, dry run | No | Yes |
| Symlinks under `-r` | Follows them and copies the target's contents | Copies them as symlinks with `-a` |
| Preserving metadata | `-p` (times, modes) | `-a`, plus `-H -A -X` |
| Learning curve | Same as `cp` | Hundreds of options, trailing slash rules |

A few rows need more than a table cell.

**Speed.** For a single big file copied for the first time, they are about equal: both push
bytes through one SSH connection, and the limit is usually the network or the SSH cipher on
one CPU core. rsync pulls ahead in three cases: when most of the data is already at the
destination (re-runs, backups, deploys), when the transfer gets interrupted (rsync resumes,
`scp` starts over), and usually with many small files, because rsync streams the file list and
contents in a pipeline instead of doing a round trip per file.

**Security.** One answer on that thread says "scp is more secure, you have to use
`rsync --rsh=ssh` to match it." That's outdated: rsync has defaulted to SSH for many years,
and `rsync file host:path` is exactly as encrypted as `scp`. The caveat is the double-colon
syntax (`host::module` or `rsync://host/module`), which talks to an rsync daemon over plain
TCP. That is fine on a trusted cluster network where you want maximum speed, but not on the
open internet.

**Integrity.** Another answer says rsync is "a copy with a guarantee" because of the whole-file
checksum, and that `scp` may corrupt large files. Both run over SSH, and SSH authenticates
every packet, so corruption *on the wire* gets caught either way. What rsync adds is a check
that the reconstructed file matches the source, which matters because it's assembling the file
from pieces. Neither tool re-reads the file from the destination disk afterwards. If you need
to be sure, run a second pass with `rsync -avc --dry-run` (it lists no files if every checksum
matches) or compare `sha256sum` on both sides.

**Availability.** This is `scp`'s real advantage. Every machine with `sshd` accepts `scp`.
Minimal container images, appliances and some locked-down servers have no `rsync` binary, and
there it fails with `rsync: command not found` on the remote side.

### So when do I use which?

Honestly, rsync, almost always. `rsync -avhP` does everything `scp -rp` does, plus resume and
progress. I reach for `scp` when:

- it's one small file and I'm typing it once,
- the other side doesn't have rsync,
- I'm copying between two remote hosts without wanting to think about it (`scp a:x b:`).

Everything recurring (cron jobs, backups, deploys, syncing a dataset to a cluster, re-copying
a directory after changing three files) goes through rsync.

## Resuming big transfers

If a 50 GB copy dies at 80% over `scp`, you start again from zero. With rsync:

```bash
rsync -avhP user@server:/data/checkpoint.tar .
# connection drops... just run the exact same command again
rsync -avhP user@server:/data/checkpoint.tar .
```

`--partial` (part of `-P`) keeps the half-transferred file instead of deleting it, and the next
run uses it as the "old version" for delta transfer, so only the missing part travels. Two
related options:

- `--partial-dir=.rsync-partial` keeps partial files in a hidden directory so a half-written
  file never sits at the real path.
- `--append-verify` is for files that only ever grow (logs, an interrupted download): it sends
  only the bytes past the current end of the destination file, then verifies the whole file.

If you're stuck with SSH-only tooling, `sftp` can also resume, with `reget` and `reput`.[^sftp]

[^sftp]: Inside an interactive `sftp user@host` session: `reget big.tar` resumes a download, `reput big.tar` resumes an upload.

## Going parallel

A single `rsync` (or `scp`) is one process on each side talking over one SSH connection, that
is, one TCP stream and one CPU core doing the encryption. That's fine most of the time, but it
leaves performance on the table when:

- you have **millions of small files**, so the time goes to per-file overhead (metadata,
  opening files) rather than bytes;
- the link is fast but far away (high bandwidth × latency), and one TCP stream can't fill it;
- the SSH cipher on one core is the bottleneck on a 10+ Gbit/s link between cluster nodes.

Parallelism doesn't help when the disk is the bottleneck (spinning disks get *slower* with
many concurrent readers seeking around) or when one stream already saturates the network.
Measure one stream first.

All the recipes below assume SSH key authentication; otherwise every parallel job prompts
for a password.

### GNU Parallel, one job per top-level directory

The simplest split: one rsync per entry in the source directory.

```bash
sudo apt install parallel     # Debian/Ubuntu

cd /data/src
find . -mindepth 1 -maxdepth 1 -print0 |
  parallel -0 -j 8 rsync -a {} user@remote:/data/dst/
```

GNU Parallel[^parallel] keeps eight rsyncs running at once (`-j 8`), starting a new one as
each finishes. I list the entries with `find`[^find] instead of the common
`ls src/ | parallel ...` because parsing `ls` output breaks on unusual file names.

[^parallel]: GNU Parallel runs a command once per input line, with `{}` replaced by that line, and keeps a fixed number of jobs running. `-j N`: run N jobs at once. `-0`: input items end with a NUL byte instead of a newline.
[^find]: `-mindepth 1`: skip `.` itself. `-maxdepth 1`: don't descend below the top level. `-print0`: end each name with a NUL byte, so names with spaces or newlines survive the pipe.

The weakness is balance: if one subdirectory holds 90% of the data, one job does 90% of the
work while the others finish early and sit idle.

### GNU Parallel, fixed-size batches of files

Better balance: list every file, cut the list into batches, and give each batch to its own
rsync via `--files-from`:

```bash
cd /data/src
find . -type f |
  parallel --pipe -N 2000 -j 8 rsync -a --files-from=- . user@remote:/data/dst/
```

`--pipe -N 2000` feeds 2000 lines of the file list to each job's standard input, and
`--files-from=-` makes rsync read its list from there.[^batch] `--files-from` implies `-R`
(`--relative`), so `./a/b/file` lands at `/data/dst/a/b/file` and the directory tree is kept.

[^batch]: `find -type f`: regular files only, no directories or symlinks. `--pipe`: send chunks of input on stdin instead of substituting `{}`. `-N 2000`: 2000 lines per chunk. In `--files-from=-`, the `-` means stdin; the `.` after it is the directory those paths are relative to.

A variant of this circulates widely:

```bash
find . -type f | parallel -j 10 -X rsync -zR -Ha ./{} user@remote_host:/destination_dir/
```

Two things to know about it.[^variant] The `-X` there is GNU Parallel's option (pack as many
file names as fit into each command), not rsync's `-X` for extended attributes. And `-H` can
only preserve hard links *within* one rsync run, so links whose files land in different
batches become separate copies.

[^variant]: Its rsync flags: `-z` compress, `-R` recreate each path relative to `.` at the destination, `-H` preserve hard links, `-a` archive mode.

### xargs, if GNU Parallel isn't installed

`xargs`[^xargs] is available everywhere, and with `-P` it runs several commands at once. The
catch is that `xargs` appends file names at the *end* of the command, but rsync needs the
destination last, so wrap it in `sh -c`:

[^xargs]: `xargs` reads items from stdin and turns them into arguments of a command: `printf 'a\nb\n' | xargs rm` runs `rm a b`. It exists because many commands take file names as arguments, not on stdin.

```bash
cd /data/src
find . -type f -print0 |
  xargs -0 -n 2000 -P 8 sh -c 'rsync -aR "$@" user@remote:/data/dst/' _
```

Each `sh` gets a batch of 2000 file names and passes them to rsync, with the destination
after them.[^xargs-flags]

[^xargs-flags]: `-0`: items end with a NUL byte (pairs with `find -print0`). `-n 2000`: at most 2000 items per command. `-P 8`: up to 8 commands at once. `sh -c '...' _ files...`: run the quoted script with `_` as `$0` and the files as `"$@"`.

Avoid the version you'll often see,
`find src/ -type f | xargs -P 10 -I {} rsync -av {} host:/dst/`: `-I`[^xargs-i] starts one
rsync (and one SSH handshake) **per file**, and without `-R` every file lands flat in `/dst/`,
so the directory structure is lost and files with the same name overwrite each other.

[^xargs-i]: `-I {}`: replace `{}` in the command with each input line, which forces one command per line.

### fpsync, when it's a real migration

For moving a whole filesystem (terabytes, millions of files), `fpsync` from the `fpart`
package[^fpart] does the batching for you. It crawls the source, packs files into partitions capped by count
and size, and starts rsync jobs on partitions while the crawl is still running:

[^fpart]: `fpart` walks a directory tree and splits the files into lists ("partitions") by count or total size. `fpsync` is the wrapper script that hands each list to its own rsync.

```bash
sudo apt install fpart     # Debian/Ubuntu

fpsync -n 8 -f 2000 -s 4G -v /data/src/ user@remote:/data/dst/
```

- `-n 8`: eight concurrent rsync processes (separate processes, not threads).
- `-f 2000` / `-s 4G`: at most 2000 files or 4 GB per job (those are also the defaults).
- `-o "..."` *replaces* the rsync options rather than adding to them. The default is
  `-lptgoD -v --numeric-ids`, so if you want compression, write
  `-o "-lptgoD -v --numeric-ids -z"`, not just `-o "-z"`.
- Runs can be resumed: `fpsync -l` lists previous runs and `fpsync -r <runid>` continues one.
- `-w user@host` spreads the jobs over several worker machines, if they all mount the source.

The source path must be absolute, and fpsync always copies the source's *contents* (it adds
the trailing slash for you).

### rclone, many streams without scripting

`rclone` is usually used for cloud storage, but it also speaks SFTP and runs many transfers
concurrently out of the box:

```bash
rclone copy /data/src :sftp,host=remote,user=manoj:/data/dst --transfers 16 --checkers 16 -P
```

The `:sftp,...:` part defines a remote on the fly.[^rclone] With no password or key given, rclone uses
your running `ssh-agent`. For anything permanent, set the remote up once with `rclone config`
and write `node2:/data/dst` instead. Avoid putting `pass=...` on the command line: it ends up
in your shell history, and rclone expects it obscured (`rclone obscure`) anyway.

[^rclone]: `copy`: copy new and changed files, never delete (`sync` would also delete). `--transfers 16`: 16 files in flight at once. `--checkers 16`: 16 parallel "does this file need copying?" checks. `-P`: live progress; unlike rsync's `-P`, nothing to do with partial files.

The trade-off: rclone copies whole files. A changed file is re-sent in full, with no
rsync-style delta transfer.

### Pushing the same files to many nodes

The other kind of parallel: one source, many destinations, like pushing a build or a config
to every node in a cluster.

```bash
# hosts.txt: one hostname per line
parallel -j 16 rsync -a ./release/ {}:/opt/app/ :::: hosts.txt
```

`::::` reads the arguments from a file, so this runs one rsync per host, 16 at a time.[^hosts]

[^hosts]: `{}` becomes each hostname, so `{}:/opt/app/` turns into `node1:/opt/app/` and so on. `:::` takes the arguments inline instead: `::: node1 node2 node3`.

### Things that bite in parallel

- **Finish with one plain rsync pass.** The file-list recipes copy only regular files, so empty
  directories, symlinks and directory timestamps are skipped, and parallel jobs can't safely
  use `--delete`. A final `rsync -a --delete /data/src/ user@remote:/data/dst/` fixes all of
  that, and is quick because almost everything already matches.
- **SSH connection sharing has a trade-off.** `ControlMaster`[^cm] in `~/.ssh/config` lets parallel
  jobs reuse one authenticated connection and saves the handshakes. But then they all share
  one TCP connection, which defeats the point if you went parallel to get multiple streams.
- **For a first copy of many small files, `tar` over SSH[^tar] is hard to beat:**

  ```bash
  tar -C /data/src -cf - . | ssh user@remote 'tar -C /data/dst -xf -'
  ```

  It's one continuous stream with no per-file round trips, at the cost of no resume and no
  delta. Follow it with an rsync pass and you get both: a fast bulk copy and verified
  incremental updates afterwards.

[^cm]: The three lines under `Host *`: `ControlMaster auto` (share connections), `ControlPath ~/.ssh/cm-%r@%h:%p` (socket file per user, host and port), `ControlPersist 10m` (keep it open 10 minutes after the last use).
[^tar]: `-C dir`: change into `dir` first. `-c` / `-x`: create / extract an archive. `-f -`: the archive is stdout (when creating) or stdin (when extracting), so it streams through the pipe and `ssh` without touching disk.

## Cheat sheet

| I want to... | Command |
|--------------|---------|
| Copy one file, once | `scp file host:/path/` |
| Copy a directory and keep metadata | `rsync -avh dir/ host:/path/dir/` |
| Copy a big file over a flaky link | `rsync -avhP file host:/path/` |
| Mirror a directory exactly (preview first) | `rsync -avhn --delete src/ host:/dst/`, then drop the `-n` |
| Use a different port or key | `rsync -e "ssh -p 2222 -i key" ...` / `scp -P 2222 -i key ...` |
| Move millions of files | `fpsync -n 8 /src/ host:/dst/`, then a final `rsync -a --delete` |
| Push to many hosts | `parallel -j 16 rsync -a ./dir/ {}:/dst/ :::: hosts.txt` |
| Copy when the remote has no rsync | `scp -r` (or `tar` over `ssh`) |

To sum up: `scp` is `cp` with a hostname, and `rsync` is a synchronisation tool that happens to be a
great copier as well. When in doubt, `rsync -avhP`.

{{< references >}}
