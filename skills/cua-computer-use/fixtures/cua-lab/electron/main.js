const { app, BrowserWindow } = require("electron");
const path = require("path");

// Cloud / container Linux: Chromium sandbox and GPU often fail closed.
app.commandLine.appendSwitch("no-sandbox");
app.commandLine.appendSwitch("disable-gpu");
app.commandLine.appendSwitch("disable-dev-shm-usage");

const debugPort = process.env.CUA_LAB_CDP_PORT;
if (debugPort) {
  app.commandLine.appendSwitch("remote-debugging-port", String(debugPort));
}

function create() {
  const win = new BrowserWindow({
    width: 920,
    height: 780,
    title: "Cua Lab",
    show: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });
  win.setTitle("Cua Lab");
  win.loadFile(path.join(__dirname, "..", "web", "index.html"));
}

app.whenReady().then(create);
app.on("window-all-closed", () => app.quit());
