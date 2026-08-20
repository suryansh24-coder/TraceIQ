import re
import os

path = r'c:\Users\HP\Downloads\TraceIQ\README.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove React badge
content = re.sub(r'\[!\[React\]\(.*?\)\]\(https://reactjs\.org/\)\n', '', content)

# Modify diagram text
content = content.replace(
    'strictly delineating the frontend interface from the backend processing engine',
    'showing the backend processing engine'
)

# Remove Frontend subgraph from flowchart
content = re.sub(
    r'    subgraph Frontend \[Client & Voice UI\].*?    end\n',
    '',
    content,
    flags=re.DOTALL
)

# Update relations in flowchart
content = content.replace('    Mic --> VoiceUI\n', '')
content = content.replace('    VoiceUI --> React\n', '')
content = content.replace('    React -->|POST /investigate| API\n', '    User -->|POST /investigate| API\n')
content = content.replace('    VoiceAPI -->|Audio Data| React\n', '    VoiceAPI -->|Audio Data| User\n')
content = content.replace('    React --> Playback\n', '')
content = content.replace('    Playback -->|Speaks Findings| User\n', '')
content = content.replace('    User -->|Speaks| Mic\n', '')

# Sequence diagram
content = content.replace('    participant UI as Frontend (React + Voice)\n', '')
content = content.replace('    SRE->>UI: Speaks Investigation Query\n', '')
content = content.replace('    UI->>API: POST /investigate\n', '    SRE->>API: POST /investigate\n')
content = content.replace('    API-->>UI: Return Structured Result\n', '    API-->>SRE: Return Structured Result\n')
content = content.replace('    UI->>SRE: Voice UI presents result\n', '')

# Remove frontend tech stack
content = re.sub(
    r'### \*\*Frontend & User Interface\*\*\n- \*\*Framework:\*\* `React` & `Vite` - Highly responsive, component-driven dashboard\.\n- \*\*Voice UI:\*\* Custom waveform and voice console visualization\.\n\n',
    '',
    content
)

# Remove frontend from project structure
content = re.sub(
    r'├── frontend/.*?│\n',
    '',
    content,
    flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("README file updated successfully.")
# hello world