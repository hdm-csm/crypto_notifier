"""Command string constants for Discord and Telegram bots."""

# Favorites Commands
COMMAND_ADD_FAV = "add_fav"
COMMAND_LIST_FAVS = "list_favs"
COMMAND_REMOVE_FAV = "remove_fav"
COMMAND_DROP_FAVS = "drop_favs"

# Notifications Commands
COMMAND_ADD_NOTIF = "add_notif"
COMMAND_LIST_NOTIFS = "list_notifs"
COMMAND_REMOVE_NOTIF = "remove_notif"
COMMAND_DROP_NOTIFS = "drop_notifs"

# Settings/Currency Commands
COMMAND_GET_VS = "get_vs"
COMMAND_LIST_VS = "list_vs"
COMMAND_SET_VS = "set_vs"

# Crypto Info Commands
COMMAND_INDEX = "index"
COMMAND_LIST = "list"

# Command examples for error messages
COMMAND_EXAMPLES = {
    COMMAND_ADD_FAV: f"\n`/{COMMAND_ADD_FAV} Bitcoin`",
    COMMAND_REMOVE_FAV: f"\n`/{COMMAND_REMOVE_FAV} Bitcoin`",
    COMMAND_LIST_FAVS: f"\n`/{COMMAND_LIST_FAVS}`",
    COMMAND_DROP_FAVS: f"\n`/{COMMAND_DROP_FAVS}`",
    COMMAND_ADD_NOTIF: f"\n`/{COMMAND_ADD_NOTIF} Bitcoin USD above 50000`",
    COMMAND_LIST_NOTIFS: f"\n`/{COMMAND_LIST_NOTIFS}`",
    COMMAND_REMOVE_NOTIF: f"\n`/{COMMAND_REMOVE_NOTIF} <notification_id>`",
    COMMAND_DROP_NOTIFS: f"\n`/{COMMAND_DROP_NOTIFS}`",
    COMMAND_GET_VS: f"\n`/{COMMAND_GET_VS}`",
    COMMAND_LIST_VS: f"\n`/{COMMAND_LIST_VS}`",
    COMMAND_SET_VS: f"\n`/{COMMAND_SET_VS} USD`",
    COMMAND_INDEX: f"\n`/{COMMAND_INDEX} Bitcoin`",
    COMMAND_LIST: f"\n`/{COMMAND_LIST}`",
}
