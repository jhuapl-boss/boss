# Django Migrations

Developers are responsible for running `makemigrations` and committing the resulting migration files when they change a model object. The prereqs for running `makemigrations` are:

* Install the Python libraries in `requirements.txt`
* Install [ndingest](https://github.com/jhuapl-boss/ndingest)
* Create `/etc/boss/` and place of a copy of [boss.config](https://github.com/jhuapl-boss/boss-tools/blob/integration/bossutils/boss.config.default) in the directory (The values can be blank, the file and keys just need to be there)

After these are finished then run `makemigrations.sh` to generate any new migration files
