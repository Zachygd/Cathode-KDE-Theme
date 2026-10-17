// Cathode: Windows 98 style desktop layout.
// Teal desktop with icons, one 34px opaque taskbar at the bottom:
// [Start] [Quick Launch] [Task buttons ..........] [Tray] [Clock]

function has(plugin) {
    return knownWidgetTypes.indexOf(plugin) !== -1;
}

function desktopFileUrl(id) {
    var path = applicationPath(id);
    return path ? "file://" + path : "";
}

// ---- Desktop -------------------------------------------------------------
var allDesktops = desktopsForActivity(currentActivity());
for (var i = 0; i < allDesktops.length; i++) {
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.color";      // plain Win98 teal
    d.currentConfigGroup = ["Wallpaper", "org.kde.color", "General"];
    d.writeConfig("Color", "0,72,72");
    d.currentConfigGroup = ["General"];
    d.writeConfig("iconSize", 1);        // 1 = 32px desktop icons, like 98
    d.writeConfig("arrangement", 1);     // arrange in columns from the top-left
    d.writeConfig("alignment", 0);
}

// ---- Taskbar -------------------------------------------------------------
var panel = new Panel;
panel.location = "bottom";
panel.height = 34;                       // Cathode standard: 3px margin + 28px buttons + 3px margin
panel.floating = false;
panel.opacity = "opaque";
panel.lengthMode = "fill";
panel.hiding = "none";

// Start button. "Cathode Start" is Plasma's cascading Application Menu (Kicker)
// patched by the installer so the button stays pushed in while the menu is open.
var startPlugin = has("org.cathode.startmenu") ? "org.cathode.startmenu"
                : has("org.kde.plasma.kicker") ? "org.kde.plasma.kicker" : "org.kde.plasma.kickoff";
var startImage = userDataPath("data", "cathode/start/cathode.png");
if (!fileExists(startImage)) {
    startImage = "/usr/share/cathode/start/cathode.png";
}
var start = panel.addWidget(startPlugin);
start.currentConfigGroup = ["General"];
start.writeConfig("icon", "start-here-cathode");
if (fileExists(startImage)) {
    start.writeConfig("useCustomButtonImage", true);
    start.writeConfig("customButtonImage", startImage);
}
start.writeConfig("showRecentApps", false);
start.writeConfig("showRecentDocs", false);
start.writeConfig("showRecentFolders", false);
start.writeConfig("alphaSort", true);
start.writeConfig("useExtraRunners", false);   // search lists apps only, in one column
start.writeConfig("menuLabel", "Start");   // only used if Kickoff is the fallback

// Quick Launch (needs kdeplasma-addons)
if (has("org.kde.plasma.quicklaunch")) {
    var urls = [];
    ["org.kde.dolphin.desktop", "org.kde.konsole.desktop"].forEach(function (id) {
        var u = desktopFileUrl(id);
        if (u) urls.push(u);
    });
    var browser = defaultApplication("browser", true);
    if (browser && browser.indexOf(".desktop") !== -1) {
        var bu = desktopFileUrl(browser);
        if (bu) urls.splice(0, 0, bu);
    }
    var ql = panel.addWidget("org.kde.plasma.quicklaunch");
    ql.currentConfigGroup = ["General"];
    ql.writeConfig("launcherUrls", urls);
    ql.writeConfig("maxSectionCount", 1);
    ql.writeConfig("showLauncherNames", false);
    ql.writeConfig("enablePopup", false);
}

// Task buttons: icon + title, one per window, no grouping, no pinned launchers
var tasks = panel.addWidget("org.kde.plasma.taskmanager");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", []);
tasks.writeConfig("groupingStrategy", 0);
tasks.writeConfig("taskHoverEffect", false);
tasks.writeConfig("maxTextLines", 1);
tasks.writeConfig("taskMaxWidth", 1);
tasks.writeConfig("showOnlyCurrentDesktop", true);
tasks.writeConfig("indicateAudioStreams", false);
tasks.writeConfig("highlightWindows", false);

// Tray: 16px icons like 98 (the default 22px icons crowd the sunken clock box)
var tray = panel.addWidget("org.kde.plasma.systemtray");
tray.currentConfigGroup = ["General"];
tray.writeConfig("iconSize", 0);
tray.writeConfig("scaleIconsToFit", false);
tray.writeConfig("iconSpacing", 1);

// Clock. Cathode Clock draws the sunken 98 notification-area box around itself
// and the tray; fall back to Plasma's clock if it isn't installed.
if (has("org.cathode.clock")) {
    panel.addWidget("org.cathode.clock");
} else {
    var clock = panel.addWidget("org.kde.plasma.digitalclock");
    clock.currentConfigGroup = ["Appearance"];
    clock.writeConfig("showDate", false);
    clock.writeConfig("showSeconds", 0);
}
