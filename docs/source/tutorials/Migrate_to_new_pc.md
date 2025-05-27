# Move DVM to new computer

In order to move all the data stored in docker volumes from one computer to another the easiest way is using Docker Desktop.

In Docker Desktop under Volumes a list of all volumes should be displayed. Only two volumes are of interest:

* dvm_app_media
* dvm_db_data_v17

The volumes may have a prefix of the folder from which docker compose is run and *vm_db_data_v17* may have another number depending on the version of the database used.

By clicking on a volume and choosing the *Exports* menu and clicking the button *Quick export* a menu for saving the data will appear. Here choose local file and give it a name and select where to save it. Depending on the volume and how many videos are stored this may take some time.

When both volumes are saved the files can be moved to the new computer.

On the new computer start *DVM* which will create the volumes. Then in docker desktop choose a volume and click *Import*. Here select the saved file for the corresponding volume and click import. Again this may take some time.

When this is done for both volumes *DVM* is ready on the new computer and should contain all data.
