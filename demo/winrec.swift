// Records one app's main window to an .mp4, even when other windows cover it.
// Usage: swift demo/winrec.swift "<app name>" out.mp4   (stop with Ctrl-C / SIGINT)
import Foundation
import ScreenCaptureKit
import AppKit
_ = NSApplication.shared
setvbuf(stdout, nil, _IONBF, 0)

let args = CommandLine.arguments
guard args.count == 3 else { print("usage: winrec <app name> <out.mp4>"); exit(2) }
let appName = args[1], out = URL(fileURLWithPath: args[2])

final class Rec: NSObject, SCRecordingOutputDelegate {
    var stream: SCStream?
    func start() async throws {
        print("listing windows")
        let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: false)
        let wins = content.windows.filter { $0.owningApplication?.applicationName == appName && $0.windowLayer == 0 }
        guard let win = wins.max(by: { $0.frame.width * $0.frame.height < $1.frame.width * $1.frame.height })
        else { print("no window for \(appName)"); exit(1) }
        let cfg = SCStreamConfiguration()
        cfg.width = Int(win.frame.width * 2); cfg.height = Int(win.frame.height * 2)
        cfg.minimumFrameInterval = CMTime(value: 1, timescale: 30)
        cfg.showsCursor = true
        let s = SCStream(filter: SCContentFilter(desktopIndependentWindow: win), configuration: cfg, delegate: nil)
        let ro = SCRecordingOutputConfiguration()
        ro.outputURL = out; ro.outputFileType = .mp4
        try s.addRecordingOutput(SCRecordingOutput(configuration: ro, delegate: self))
        try await s.startCapture()
        stream = s
        print("recording \(appName) \(Int(win.frame.width))x\(Int(win.frame.height)) -> \(out.path)")
    }
}

let rec = Rec()
Task { do { try await rec.start() } catch { print("error: \(error)"); exit(1) } }
signal(SIGINT, SIG_IGN)
let sig = DispatchSource.makeSignalSource(signal: SIGINT, queue: .main)
sig.setEventHandler {
    Task { try? await rec.stream?.stopCapture(); try? await Task.sleep(nanoseconds: 500_000_000); print("saved"); exit(0) }
}
sig.resume()
NSApplication.shared.run()
