<script setup></script>

<template lang="pug">
.content    
  h2 Merlino
  p A stealth-obfuscated GoLang agent with AV evasion
hr

.content
  p 
    | The Merlino agent is an obfuscated variant of Sandcat, compiled with GoHide to evade 
    | antivirus detection. It removes IoC strings, uses advanced LDFLAGS, and includes AMSI/ETW 
    | bypass techniques. Merlino communicates with the server over HTTP(S) by default.
  p.has-text-weight-bold To deploy a Merlino agent, go to the Agents tab.
</template>
