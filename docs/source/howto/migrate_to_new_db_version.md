# Migrate to new DB version

When end of life is reached for the PostgreSQL database version it is necessary to migrate already stored data to the new version.

To migrate to the new database version download *docker-compose.db_upgrade.yml* from the [github release](https://github.com/egemose/DroneVideoMeasure/releases/latest). Run the following command:

```bash
docker compose -f docker-compose.db_upgrade.yml up
```

This will start the old PostgreSQL container and make a database dump, then start the new PostgreSQL container and create the database from the dump. Depending on the size of the database it may take some time, but after some time the output in the terminal will stop changing and the process should be done.
