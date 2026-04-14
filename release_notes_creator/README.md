# sw.conmod.integration.release.documentation_scripts

## usage
### All Arguments
```commandline
main_documentation_generation.py [--gui GUI_ARG] [--output_folder OUTPUT_FOLDER]
                                 [--rrr_confluence_link RRR_CONFLUENCE_LINK] [--delivery_type DELIVERY_TYPE]
                                 [--jazz_test_plan_id TEST_PLAN_ID] [--win_uid WIN_UID]
                                 [--win_passwd WIN_PASSWD] [--klocwork_user KLOCWORK_USER]
                                 [--klocwork_token KLOCWORK_TOKEN] [--artifactory_user ARTIFACTORY_USER]
                                 [--artifactory_token ARTIFACTORY_TOKEN]
```
```commandline
optional arguments:
  -h, --help            show help message and exit
  --gui GUI_ARG         If you will run the script in 'GUI' mode => 'GUI_ARG'='True'
  --output_folder OUTPUT_FOLDER
                        Folder for all outputs
  --rrr_confluence_link RRR_CONFLUENCE_LINK
                        The Confluence URL to the RRR-(Pre)-Release_Version. It should looks like 'https://confluence
                        .auto.continental.cloud/display/CMP/RRR+cl43-3.3.323.3+-+2023+cw23.1+Release+-+PROD-Signed'
  --delivery_type DELIVERY_TYPE
                        Set 'Continental Release' or 'Pre Release'
  --jazz_test_plan_id TEST_PLAN_ID
                        The Testplan ID from IBM Jazz
  --win_uid WIN_UID     Your Windows User ID
  --win_passwd WIN_PASSWD
                        Your Windows User Password
  --klocwork_user KLOCWORK_USER
                        Your Klocwork User name
  --klocwork_token KLOCWORK_TOKEN
                        Your Klocwork token
  --artifactory_user ARTIFACTORY_USER
                        Your Artifactory user
  --artifactory_token ARTIFACTORY_TOKEN
                        Your Artifactory token

```
### Run commands
#### For help
`main_documentation_generation.py -h`

#### For Gui Mode
```commandline
main_documentation_generation.py --gui True
```


#### For run from command line
##### For run in Conmod CI with using of credentials from artifactory file in Docker container
```commandline
main_documentation_generation.py --output_folder <OUTPUT_FOLDER> --rrr_confluence_link <RRR_CONFLUENCE_LINK> --delivery_type <DELIVERY_TYPE> --jazz_test_plan_id <TEST_PLAN_ID> --win_uid <WIN_UID> --win_passwd <WIN_PASSWD> --klocwork_user <KLOCWORK_USER> --klocwork_token <KLOCWORK_TOKEN>
```
##### For run in Conmod CI with using of credentials from artifactory file in Docker container (without jazz testplan id available)
```commandline
main_documentation_generation.py --output_folder <OUTPUT_FOLDER> --rrr_confluence_link <RRR_CONFLUENCE_LINK> --delivery_type <DELIVERY_TYPE> --win_uid <WIN_UID> --win_passwd <WIN_PASSWD> --klocwork_user <KLOCWORK_USER> --klocwork_token <KLOCWORK_TOKEN>
```

#### For run in command line mode with set of artifactory credentials over command line
```commandline
main_documentation_generation.py --output_folder <OUTPUT_FOLDER> --rrr_confluence_link <RRR_CONFLUENCE_LINK> --delivery_type <DELIVERY_TYPE> --jazz_test_plan_id <TEST_PLAN_ID> --win_uid <WIN_UID> --win_passwd <WIN_PASSWD> --klocwork_user <KLOCWORK_USER> --klocwork_token <KLOCWORK_TOKEN> --artifactory_user <ARTIFACTORY_USER> --artifactory_token <ARTIFACTORY_TOKEN>
```

#### For run in command line mode with set of artifactory credentials over command line (without jazz testplan id available)
```commandline
main_documentation_generation.py --output_folder <OUTPUT_FOLDER> --rrr_confluence_link <RRR_CONFLUENCE_LINK> --delivery_type <DELIVERY_TYPE> --win_uid <WIN_UID> --win_passwd <WIN_PASSWD> --klocwork_user <KLOCWORK_USER> --klocwork_token <KLOCWORK_TOKEN> --artifactory_user <ARTIFACTORY_USER> --artifactory_token <ARTIFACTORY_TOKEN>
```
