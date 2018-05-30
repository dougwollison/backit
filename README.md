# backit

**backit** is a utility kit for creating incremental backups via rsync, which can then be packaged up and exported to Backblaze B2.

## Installation

1. Clone or unzip the repository, I suggest storing everything in `/opt/backit`.
2. Execute (or run with `bash`) the `install.sh` script to A) install aliases to the `/bin` scripts, or B) add the `/bin` folder to your user's `PATH`.
3. Write up your `.conf` and `.rules` files you want, stored in `/conf` of backit's directory, referencing the included example files.
4. Test your backup with `backit-up PROJECT test`, replacing PROJECT with the name of the `.conf` file you setup.
5. Add cron jobs to run your backups, archive exports, and cleaning as you see fit.
6. Optional, `source` the `bash_tools.sh` file into your user's `.bash_profile`, for handy autocomplete for the commands.

## Configuration

The config files are required to handle things like where to back up from/to, credentials for B2, etc.

For setups with multiple backups, it's recommended to have shared settings in a `default.conf` file, and the project specific ones in their own files.

The config options are:

### Storage Options

**keep** - How many backups to keep during cleanup. Leave out or set to 0 to keep all backups.

**tarballs_dir** - Where to store the tar-gzipped archives of the backups while they're being uploaded to B2.

### rsync Options

**connection** - The SSH connection to use. NOTE: username is specified; a pure SSH alias won't work (rsync's fault, not mine)

**source_root** - What base directory to backup from. Defaults to root (`/`)

**backups_root** - What directory to store all backups for this project in.

**filter** - The full path (absolute) to the rsync rules file. See `rsync.rules-example` for an example.

**log_file** - The full path (absolute) to the rsync log file. Useful for debugging.

### Backblaze Options

**account_id**, **account_key** - The API credentials for your B2 account.

**bucket** - The name of the bucket your uploading to.

**parent_folder** - A subdirectory within the bucket to upload to.

**separate_folders** - A colon-separated list of folders within the backup to archive separately, rather than one large tar file.
