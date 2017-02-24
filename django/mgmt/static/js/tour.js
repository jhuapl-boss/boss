var tour = {
    id: "boss-tour",
    steps: [{
        title: "Welcome",
        content: "Let's step through the basic components of the Boss Management Console",
        target: "tour_btn",
        placement: "left"
        },
        {
            title: "Home Page",
            content: "Click on the Boss Logo to go to the homepage",
            target: "boss_logo",
            placement: "bottom",
            multipage: true,
            onNext: function () {
                window.location = MGMT_ROOT
            }
        },
        {
            title: "System Notices",
            content: "If there are any system level notices (e.g. maintenance windows) they will appear here.",
            target: "alerts_section",
            placement: "bottom",
            xOffset: "center"
        },
        {
            title: "Updates",
            content: "This section will display update blog posts highlighting important changes.",
            target: "updates_section",
            placement: "top",
            xOffset: "center"
        },
        {
            title: "Tools",
            content: "This section contains useful links to tools and documentation.",
            target: "tools_section",
            placement: "top",
            xOffset: "center",
            onNext: function () {
                 $("#user-dropdown").dropdown("toggle");
            }
        },
        {
            title: "API Token",
            content: "To get a long-lived API token click 'API Token' in the dropdown",
            target: "li#token_dropdown",
            placement: "left",
            delay: 500,
            multipage: true,
            onNext: function () {
                window.location = MGMT_ROOT + "token"
            }
        },
        {
            title: "Generate Token",
            content: "Click `Generate Token` to create a new token. <br><br>Click 'Revoke Token' to delete the token from the system",
            target: "gen_token_btn",
            placement: "right"
        },
        {
            title: "Copy Token",
            content: "Copy the token to use with `intern` or to directly call the API. See the documentation for more details.",
            target: "token_val",
            placement: "bottom",
            multipage: true,
            onNext: function () {
                window.location = MGMT_ROOT + "resources"
            }
        },
        {
            title: "Manage Resources",
            content: "The Manage Resources page lets you create, modify, and delete resources. Resources are used organize data in the Boss",
            target: "mng_resources_btn",
            placement: "bottom"
        },
        {
            title: "Collections",
            content: "Collections group together related datasets, typically from the same animal",
            target: "collections_panel",
            placement: "bottom",
            xOffset: "center"
        },
        {
            title: "Add a Collection",
            content: "You can create a new collection if you have the 'resource-manager' role",
            target: "collections_toolbar",
            placement: "right"
        },
        {
            title: "Collections Table",
            content: "This table will list the collections to which you have at least read permissions. <br><br> Clicking on 'Details' will show the detail page for the collection. Clicking 'Delete' will mark the collection for deletion",
            target: "collection_table",
            placement: "top",
            xOffset: "center",
            width: 400
        },
        {
            title: "Coordinate Frames",
            content: "Coordinate Frames set the spatial bounds that a dataset can fill",
            target: "coord_panel",
            placement: "bottom",
            xOffset: "center"
        },
        {
            title: "Add a Coordinate Frame",
            content: "You can create a new coordinate frame if you have the 'resource-manager' role",
            target: "coord_toolbar",
            placement: "right"
        },
        {
            title: "Coordinate Frame Table",
            content: "This table will list ALL coordinate frames. <br><br> Clicking on 'Details' will show the detail page for the coordinate frame.<br>Clicking 'Delete' will mark the collection for deletion only if you created it.",
            target: "coord_table",
            placement: "top",
            xOffset: "center",
            width: 400,
            multipage: true,
            onNext: function () {
                window.location = MGMT_ROOT + "groups"
            }
        },
        {
            title: "Manage Groups",
            content: "The Manage Groups page lets you create and delete groups and modify members of groups. <br><br>Groups are used to link users to resources and permission sets. <br><br>Through this you can control access to your data, or even make it publicly accessible!",
            target: "mng_groups_btn",
            width: 400,
            placement: "bottom"
        },
        {
            title: "Add a Group",
            content: "You can create a new group if you have the 'resource-manager' role",
            target: "groups_toolbar",
            placement: "right"
        },
        {
            title: "Group Table",
            content: "This table will list the groups to which you are in or are a maintainer. <br><br> Clicking on 'Details' will show the detail page for the group, letting you add/remove users. <br><br>Clicking 'Delete' will delete the group",
            target: "group_table",
            placement: "top",
            xOffset: "center",
            width: 400
        }
    ]
};

function add_user_manager(tour){
    tour.steps.push(
        {
            title: "Manage Users",
            content: "The Manage Users page lets you create users, and more importantly modify user roles. <br><br>User roles grant elevated permissions to peform certain actions. <br><br>'resource-manager' is required to create NEW resources in the Boss <br><br>'user-manager' is required to access this section of the console.",
            target: "mng_users_btn",
            width: 400,
            placement: "bottom",
            xOffset: "center",
            multipage: true,
            onNext: function () {
                window.location = MGMT_ROOT + "users"
            }
        },
        {
            title: "Add a User",
            content: "Typically a user will self-register, but you can manually add a user to the Single Sign-On service",
            target: "users_toolbar",
            placement: "right"
        },
        {
            title: "Users Table",
            content: "This table will list all users. <br><br> Clicking on 'Manage Roles' will show user's details and let you add or remove roles.<br><br><strong>Note:</strong> A user must logout and back in for the change to be applied.<br><br>Clicking 'Delete' will delete the user, but can only be done by an Administrator",
            target: "users_table",
            placement: "top",
            xOffset: "center",
            width: 400
        });
    return tour
}

function add_end(tour){
    tour.steps.push({
        title: "Let's Do This!",
        content: "That should cover the basics. <br>Check out the documentation for more details and <strong>happy peta-scale neurosciencing!</strong>",
        target: "mng_resources_btn",
        placement: "bottom",
        width: 400
    });
    return tour
}

function start_tour(roles) {
    hopscotch.endTour();
    hopscotch.startTour(tour);
}