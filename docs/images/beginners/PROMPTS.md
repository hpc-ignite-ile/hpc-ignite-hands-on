# Generated beginner illustrations

Generated on 2026-09-26 using the built-in image generation tool (not CLI fallback), following the imagegen skill. These are conceptual teaching illustrations, not actual screenshots or measured results. English labels are paired with Thai captions and text equivalents in the tutorials. The images were visually reviewed for text, flow direction and scope.

## tutorial-overview.png

Saved asset: [tutorial-overview.png](tutorial-overview.png).

Final prompt:

```text
Use case: scientific-educational
Asset type: landscape raster illustrated overview for the HPC IGNITE beginner tutorial on ThaiSC LANTA.
Primary request: Explain what a newcomer will learn and the whole workflow, as a welcoming illustrated learning map, not a terminal screenshot.
Composition: wide landscape, white background, generous spacing, large legible English text, warm editorial science textbook illustration. Six connected numbered stations in a clear left-to-right journey with small meaningful illustrations: laptop and key; folders and data; small job ticket; scheduler queue and CPU/GPU racks; magnifier over a table and curve; stopwatch and improvement loop. Use restrained harmonious colors and strong text contrast. Below the main journey, show three small application vignettes: a people-contact network, weather and a building, an atomistic molecule.
Text verbatim:
Title "HPC IGNITE on LANTA"
Subtitle "From your laptop to a reproducible experiment"
Stations: "1 Connect", "2 Prepare", "3 Submit", "4 Run", "5 Check", "6 Improve"
Station captions respectively: "SSH access", "Code + data + environment", "Slurm job + account", "CPU / GPU allocation", "Logs + outputs + correctness", "Measure, change, repeat"
Application labels: "Agent-based models", "Weather and buildings", "Scientific computing"
Footer: "Conceptual learning map — not a record of a real run"
Constraints: accurate sequence and unambiguous arrows. Submit precedes Run. Do not imply computation runs on the login node. No fabricated metrics, no live job IDs, no cluster logo or screenshot framing. Do not include more text than specified.
```

## lanta-job-workflow.png

Saved asset: [lanta-job-workflow.png](lanta-job-workflow.png).

Final prompt:

```text
Use case: scientific-educational
Asset type: illustrated landscape raster explainer for newcomers to LANTA HPC.
Primary request: Show where commands and data belong, using a clean warm textbook illustration with laptop, small access gateway, scheduler ticket rack, CPU/GPU servers and shared storage. White backdrop, navy readable headings, calm accent colors, consistent with an introductory science handbook. Large labels, no tiny paragraphs.
Title verbatim "Where does my job run?"
Top row is one clear control path: laptop "Your laptop" --arrow labeled "SSH"--> "Login node" --arrow labeled "sbatch"--> "Slurm queue" --arrow labeled "allocation"--> "Compute nodes". Under Login node label "Edit, inspect, submit". Under Compute nodes label "Run CPU / GPU work".
Bottom row is one clear data path: laptop icon "Your laptop" --arrow labeled "rsync / scp"--> "Transfer host" --arrow--> "Project storage". Connect Project storage and Compute nodes with a bidirectional arrow labeled "Read inputs / write results". Do not draw a heavy-computation path on login or transfer hosts.
Small lower-right inset showing three simple job tickets in order: "PENDING" then "RUNNING" then "CHECK OUTPUTS".
Footer verbatim "Conceptual workflow — heavy computation belongs on allocated compute nodes"
Constraints: clean unambiguous arrowheads, no fake shell logs, no metrics or job IDs, not a screenshot, no branding logos. Clearly separate control flow from data flow.
```

## performance-learning-loop.png

Saved asset: [performance-learning-loop.png](performance-learning-loop.png).

Final prompt:

```text
Use case: scientific-educational
Asset type: landscape illustrated raster infographic for beginners learning HPC performance evaluation.
Primary request: Teach that correctness precedes optimization and measurements must be comparable. Friendly polished science textbook illustration, white background, large dark readable sans serif labels, magnifier/checklist, stopwatch, CPU-memory-GPU instruments, adjustable knob and repeat arrows. Generous whitespace.
Title verbatim "Correct first. Then faster."
Five numbered panels in reading order with arrows:
"1 Check correctness" caption "Validate outputs and inputs"
"2 Record a baseline" caption "Same data, seed and software"
"3 Measure resources" caption "Time, CPU, memory, GPU"
"4 Change one thing" caption "Threads, ranks, batch or I/O"
"5 Repeat and compare" caption "Correct + faster + efficient?"
A clean return arrow from panel 5 back to panel 1 labeled "Keep the evidence".
Bottom three illustrated evidence folders labeled "Job ID + logs", "Output files", "Resource statistics".
Footer verbatim "Conceptual guide — a successful job is not proof of correct science"
Constraints: show no numeric benchmark bars, percentages, simulated metrics, green all-passed dashboard, or speedup claims. Do not suggest more GPUs always help. Not a screenshot. All specified labels must be exact and readable.
```

## mesa-twinb-learning-map.png

Saved asset: [mesa-twinb-learning-map.png](mesa-twinb-learning-map.png).

Final prompt:

```text
Use case: scientific-educational
Asset type: landscape illustrated raster teaching diagram for the HPC IGNITE Mesa and Twin-B tutorials.
Primary request: Explain the model layers and intended feedback workflow, while clearly distinguishing beginner surrogate exercises from advanced EnergyPlus integration.
Style: welcoming modern science textbook illustration, white background, readable navy text, softly rendered building cutaway and small people agents, restrained accent colors, generous space, simple clearly labeled arrows.
Title verbatim "From agents to building co-simulation"
Left card: small person agents on a grid, label "Mesa agents", caption "People, behavior and comfort".
Middle card: a small building with thermal glow, label "Building model"; within it two vertically stacked clearly distinct options labeled "Thermal surrogate" and "EnergyPlus". Beside first option badge "Beginner exercise"; beside second badge "Advanced integration".
Draw a loop between Mesa agents and Building model: upper arrow from building to agents labeled "Indoor temperature"; lower arrow from agents to building labeled "Setpoint requests".
At upper right, weather sun/cloud icon labeled "Weather data" with one arrow entering Building model.
At lower right a clipboard and simple unlabeled sketch curve, label "Compare outputs", caption "Energy, comfort and runtime". Connect building to this clipboard.
Prominent separate bottom note verbatim "Intended coupling — validate synchronization before trusting results"
Footer verbatim "Conceptual illustration, not a verified EnergyPlus run"
Constraints: do not imply the surrogate is EnergyPlus; do not claim the advanced integration passed; no fake measured values, terminal windows, scientific validation checkmarks or HPC performance claims. Keep all arrows clear and logically correct.
```


