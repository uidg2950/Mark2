import flet as ft
import keyring as keyring

from keyring_variables import *


def gui(page: ft.Page):
    """
    The gui function is the main entry point for your application.
    It will be called by the frontend when it's time to render your app.
    The gui function must return a ft.Page object, which contains all of the elements you want to display on screen.

    :param page: ft.Page: Add controls to the window
    :return: A page object, which is then passed to the app
    """
    page.title = "Generate Pre-/Release Documentation"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_height = 1200
    page.window_width = 1500

    title_width = 200
    credentials_width = 1000
    button_width = 200

    def check_if_credential_avalaible(cred_field):
        """
        The check_if_credential_avalaible function checks if the credential is available in the keyring.
        If it is, it returns a green color and the password. If not, it returns a red color and None.

        :param cred_field: Identify the credential to be retrieved from the keyring
        :return: A tuple
        """
        passwd = keyring.get_password(SERVICE_NAME, cred_field)
        if passwd:
            return "green", passwd
        else:
            return "red", passwd

    def create_password_field(cred_field, label, pass_field=True):
        """
        The create_password_field function is used to create a password field for the credentials.
        It takes two arguments:
            cred_field - The name of the credential field that will be displayed in this text box.
            label - The label that will be displayed above this text box.

        :param cred_field: Store the name of the credential field
        :param label: Display the name of the field
        :param pass_field: Determine if the field should be a password field or not
        :return: A textfield with the appropriate label and background color
        """
        bgcolor, value = check_if_credential_avalaible(cred_field)
        return ft.TextField(label=label, bgcolor=bgcolor, width=credentials_width, password=pass_field, can_reveal_password=True,
                            data={"cred_field": cred_field}, value=value)

    release_version = create_password_field(RELEASE_VERSION, RELEASE_VERSION, pass_field=False)
    confluence_page_pre_release = create_password_field(CONFLUENCE_PAGE_PRE_RELEASE, CONFLUENCE_PAGE_PRE_RELEASE, pass_field=False)
    confluence_page_release = create_password_field(CONFLUENCE_PAGE_RELEASE, CONFLUENCE_PAGE_RELEASE, pass_field=False)
    testplan_id = create_password_field(TEST_PLAN_ID, TEST_PLAN_ID, pass_field=False)
    uid = create_password_field(UID, UID)
    win_passwd = create_password_field(WIN_PASSWD, WIN_PASSWD)
    github_token = create_password_field(GITHUB_TOKEN, GITHUB_TOKEN)
    klocwork_user = create_password_field(KLOCWORK_USER, KLOCWORK_USER)
    klocwork_token = create_password_field(KLOCWORK_TOKEN, KLOCWORK_TOKEN)
    artifactory_user = create_password_field(ARTIFACTORY_USER, ARTIFACTORY_USER)
    artifactory_token = create_password_field(ARTIFACTORY_TOKEN, ARTIFACTORY_TOKEN)

    def save_credential(e):
        """
        The save_credential function saves the credential to the keyring.
        It also updates the background color of the password field and clears its value.

        :param e: Get the data from the form
        :return: The color of the password field, and the value of it
        """
        keyring.set_password(SERVICE_NAME, e.control.data["pass_name"], e.control.data["pass_value"].value)
        e.control.data["pass_value"].bgcolor, e.control.data["pass_value"].value = check_if_credential_avalaible(e.control.data["pass_value"].data["cred_field"])
        page.update()

    def save_check_box(e):
        """
        The save_check_box function is a callback function that saves the state of the checkbox to keyring.
        It takes one argument, e, which is an event object.  The event object has a control attribute which contains
        the data dictionary for the checkbox widget that was clicked on.  This data dictionary contains a pass_name key
        which holds the name of password to be saved in keyring.

        :param e: Get the data from the checkbox
        :return: The data from the check box
        """
        keyring.set_password(SERVICE_NAME, e.control.data["pass_name"], e.data)

    def keyring_evailable(key):
        """
        The keyring_evailable function checks to see if a key is available in the keyring.
        If it is, it returns the value of that key. If not, it sets that value to &quot;false&quot; and then returns &quot;false&quot;.
        This function will be used for checking whether or not a user has entered their credentials before.

        :param key: Store the keyring password
        :return: A string
        """
        if keyring.get_password(SERVICE_NAME, key):
            return keyring.get_password(SERVICE_NAME, key)
        else:
            keyring.set_password(SERVICE_NAME, key, "false")

    def close_window():
        """
        The close_window function is called when the user clicks on the 'Close' button.
        It destroys the window and exits.

        :return: The window_destroy function
        """
        page.window_destroy()

    def add_heading(text):
        """
        The add_heading function takes a string as input and returns a formatted
            table row with the text in bold, blue, underlined font.

        :param text: Set the text of the heading
        :return: A row object
        """
        return_heading = ft.Row(
            controls=[
                ft.Text(
                    spans=[
                        ft.TextSpan(
                            text,
                            ft.TextStyle(
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLUE,
                                decoration=ft.TextDecoration.UNDERLINE,
                                size=20
                            )
                        )
                    ]
                ),
            ],
        )
        return return_heading

    page.add(
        add_heading("Credentials"),
        ft.Row(controls=[
            ft.Text("Your UID", width=title_width),
            uid,
            ft.ElevatedButton("Save this credential!", on_click=save_credential, data={"pass_name": UID, "pass_value": uid},
                              width=button_width)
        ]),
        ft.Row(controls=[
            ft.Text("Your UID password", width=title_width),
            win_passwd,
            ft.ElevatedButton("Save this credential!", on_click=save_credential, data={"pass_name": WIN_PASSWD, "pass_value": win_passwd},
                              width=button_width)
        ]),
        ft.Row(controls=[
            ft.Text("Your GitHub Token", width=title_width),
            github_token,
            ft.ElevatedButton("Save this credential!", on_click=save_credential, data={"pass_name": GITHUB_TOKEN, "pass_value": github_token},
                              width=button_width)
        ]),
        ft.Row(controls=[
            ft.Text("Your Klocwork User", width=title_width),
            klocwork_user,
            ft.ElevatedButton("Save this credential!", on_click=save_credential, data={"pass_name": KLOCWORK_USER, "pass_value": klocwork_user},
                              width=button_width)
        ]),
        ft.Row(controls=[
            ft.Text("Your Klocwork Token", width=title_width),
            klocwork_token,
            ft.ElevatedButton("Save this credential!", on_click=save_credential, data={"pass_name": KLOCWORK_TOKEN, "pass_value": klocwork_token},
                              width=button_width)
        ]),

        ft.Row(controls=[
            ft.Text("Your Artifactory User", width=title_width),
            artifactory_user,
            ft.ElevatedButton("Save this credential!", on_click=save_credential, data={"pass_name": ARTIFACTORY_USER, "pass_value": artifactory_user},
                              width=button_width)
        ]),
        ft.Row(controls=[
            ft.Text("Your Artifactory Token", width=title_width),
            artifactory_token,
            ft.ElevatedButton("Save this credential!", on_click=save_credential, data={"pass_name": ARTIFACTORY_TOKEN, "pass_value": artifactory_token},
                              width=button_width)
        ]),

        ft.Divider(height=3, color="red"),
        add_heading("Settings"),
        ft.Row(controls=[
            ft.Text("The Release version for this Document", width=title_width),
            release_version,
            ft.ElevatedButton("Save this credential!", on_click=save_credential, data={"pass_name": RELEASE_VERSION, "pass_value": release_version},
                              width=button_width)
        ]),
        add_heading("Pre_Release"),
        ft.Row(controls=[
            ft.Text("The confluence url", width=title_width),
            confluence_page_pre_release,
            ft.ElevatedButton("Save this credential!", on_click=save_credential,
                              data={"pass_name": CONFLUENCE_PAGE_PRE_RELEASE, "pass_value": confluence_page_pre_release},
                              width=button_width)
        ]),
        add_heading("Release"),
        ft.Row(controls=[
            ft.Text("The confluence url", width=title_width),
            confluence_page_release,
            ft.ElevatedButton("Save this credential!", on_click=save_credential,
                              data={"pass_name": CONFLUENCE_PAGE_RELEASE, "pass_value": confluence_page_release},
                              width=button_width)
        ]),
        ft.Row(controls=[
            ft.Text("The Testplan ID from IBM Jazz", width=title_width),
            testplan_id,
            ft.ElevatedButton("Save this credential!", on_click=save_credential,
                              data={"pass_name": TEST_PLAN_ID, "pass_value": testplan_id},
                              width=button_width)
        ]),
        ft.Divider(height=3, color="red"),
        add_heading("What should be run"),
        ft.Checkbox(
            label="Create Pre-Release markdown file",
            value=keyring_evailable(BOX_PRE_RELEASE_MD),
            on_change=save_check_box,
            data={"pass_name": BOX_PRE_RELEASE_MD}
        ),
        ft.Checkbox(
            label="Create Release note json file",
            value=keyring_evailable(BOX_RELEASE_NOTE_JSON),
            on_change=save_check_box,
            data={"pass_name": BOX_RELEASE_NOTE_JSON}
        ),
        ft.ElevatedButton("Run script", on_click=close_window, width=700, height=30, bgcolor="green")
    )
