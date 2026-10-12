# Antigravity Restructuring + UI Redesign Prompt — Admin-Only Logistics Dashboard

You previously built this project based on `Development_Playbook.md`.

We are now making a **critical structural pivot to both the frontend architecture and the data/routing pipeline** ahead of a demo tomorrow (10–15 minute presentation to judges).

Read this entire prompt fully before making any changes.

I will also attach **three UI reference images** with this prompt:

- `Reference 1` → Active Dashboard
- `Reference 2` → Comparison Dashboard
- `Reference 3` → Analysis Dashboard

These images are **visual design references**, not screenshots that must be copied pixel-for-pixel.

The goal is to reproduce their:
- visual hierarchy
- layout philosophy
- spacing
- typography
- restrained color palette
- information density
- navigation structure
- map prominence
- component organization
- overall premium/technical feel

Do NOT blindly copy every piece of text, number, route, vehicle, or metric visible in the reference images. The actual application data must come from the project's real data model and simulation.

---

# 0. CRITICAL EXECUTION RULE — WORK IN PHASES

**DO NOT perform the entire restructuring in one operation.**

This project must be implemented in clearly separated phases.

After completing each phase:

1. Stop.
2. Inspect the implementation.
3. Run/build the application.
4. Verify that the existing functionality has not been unnecessarily broken.
5. Report:
   - what was changed
   - which files/modules were changed
   - which files/modules were removed
   - what functionality is now working
   - any assumptions made
   - any issues or limitations discovered
6. Show me the result for review.
7. **WAIT FOR MY APPROVAL.**
8. Only then proceed to the next phase.

Never automatically continue to the next phase without my approval.

---

# PHASE 0 — CODEBASE AUDIT + MIGRATION PLAN

Before modifying the application:

- Inspect the entire existing codebase.
- Understand the current frontend architecture.
- Understand routing/data-flow architecture.
- Locate the existing:
  - driver panel
  - admin panel
  - fleet/vehicle modules
  - route assignment modules
  - analytics modules
  - map components
  - routing services
  - TomTom integration
  - OSM/road graph integration
  - QIGA implementation
  - QPSO implementation
  - simulation/timing logic
  - database/storage layer
  - API layer
  - authentication
  - existing seed/demo data

Do not assume filenames.

Use the **actual existing filenames and modules** when describing the migration.

### At the end of Phase 0, provide:

## Existing Architecture

Explain briefly:

- frontend structure
- backend structure
- data model
- routing pipeline
- optimization pipeline
- simulation pipeline
- map implementation
- persistence/storage

## Proposed Architecture

Map the existing modules to:

```text
Admin Application
│
├── Active Dashboard
│   ├── Live Map
│   ├── Simulation Controls
│   ├── Fleet Status
│   ├── Delivery Status
│   ├── SLA Status
│   ├── Next Stop Events
│   └── Live KPIs
│
├── Comparison Dashboard
│   ├── Preset Selection
│   ├── Strategy Metrics
│   ├── Route Preview
│   ├── Strategy Insights
│   ├── Vehicle Assignments
│   └── Assign Selected Strategy
│
└── Analysis Dashboard
    ├── Historical KPIs
    ├── Performance Trends
    ├── Preset Comparison
    ├── Session History
    └── Key Insights
```

Also explicitly identify:

- what will be removed
- what will be refactored
- what will be newly created
- what will remain unchanged

### IMPORTANT

Do not modify the application yet during Phase 0.

Wait for approval.

---

# 1. HIGH-LEVEL PRODUCT CHANGE

The application is now a **single admin-only logistics operations platform**.

## Remove the Driver Experience

Remove the driver panel/driver-facing workflow entirely.

There should be no separate driver dashboard, driver navigation, driver delivery interface, or driver-specific workflow.

Drivers may still exist as **data associated with vehicles**, if required internally, but they are no longer a user-facing part of the application.

---

# 2. FINAL NAVIGATION STRUCTURE

The admin application must have exactly **three primary navigation destinations**:

1. **Active Dashboard**
2. **Comparison Dashboard**
3. **Analysis Dashboard**

The old navigation such as:

- Fleet Overview
- Route Assignment
- Vehicles & Drivers
- Analytics & Trends
- Live Traffic & Engine

must NOT remain as separate primary dashboard pages.

Their useful functionality should be absorbed into the three new dashboards.

Do not simply rename the old pages.

The information architecture must genuinely become:

```text
ACTIVE
COMPARISON
ANALYSIS
```

The three attached reference images demonstrate this structure.

---

# 3. CORE DATA MODEL

## 3.1 Warehouses

Exactly **3 fixed warehouses**.

Choose strategically distributed locations across Pune primarily for good visual map coverage.

They do not need to correspond to real industrial zones.

The same three warehouse identities should be consistently used throughout:

- Active Dashboard
- Comparison Dashboard
- Analysis Dashboard
- routing engine
- historical sessions

---

## 3.2 Vehicles

Use **10–12 vehicles total**.

Each vehicle must have:

- unique vehicle ID
- fixed capacity
- capacity between **4 and 7 parcels**
- capacity assigned once and persisted
- varying capacities across the fleet

Example:

```text
Van-01 → 5 parcels
Van-02 → 6 parcels
Van-03 → 4 parcels
Van-04 → 7 parcels
...
```

Do not make every vehicle identical.

Each vehicle is associated with **exactly one warehouse per simulated day**.

A vehicle cannot serve parcels from multiple warehouses within the same session/day.

---

## 3.3 Daily Vehicle Starting Positions

Vehicle starting positions must reset at the beginning of every simulated day.

Do NOT carry yesterday's ending coordinates into the next day.

Generate strategically scattered starting positions around Pune.

The starting positions should intentionally create different repositioning scenarios:

- some vehicles close to their warehouse
- some moderately far away
- some significantly farther away

This is important because the demo should visibly demonstrate:

```text
Current Vehicle Location
        ↓
Repositioning Leg
        ↓
Assigned Warehouse
        ↓
Delivery Route
```

---

## 3.4 Delivery Sheets

Generate multiple pre-generated demo days.

Each day must have **50–60 parcels**.

Every parcel must contain at minimum:

```text
parcel_id
source_warehouse_id
delivery_latitude
delivery_longitude
sla_start
sla_end
status
```

Delivery locations should be strategically distributed across Pune.

Do NOT simply generate random coordinates that cluster unnaturally.

---

## 3.5 SLA Windows

Every parcel must have a **narrow SLA delivery window**.

Use approximately **2–3 hour windows** distributed across the simulated working day.

Example:

```text
08:30 – 10:30
10:00 – 12:30
11:30 – 14:00
13:00 – 15:00
15:00 – 17:30
```

Avoid giving every parcel a generic:

```text
08:00 – 18:00
```

The SLA windows are important because they provide genuine optimization signal for the SLA-Priority strategy.

---

## 3.6 Historical Demo Data

Pre-seed **2–3 historical sessions** so that the Analysis Dashboard is populated immediately.

Every newly assigned/run day must automatically produce a historical record.

---

# 4. ROUTING PIPELINE

The routing architecture must follow this pipeline for every vehicle.

## Step 1 — Road Snapping

Snap:

- vehicle starting position
- warehouse position
- delivery locations

to the available road network.

---

## Step 2 — Repositioning Leg

Vehicle travels:

```text
Current Starting Position
            ↓
Assigned Warehouse
```

This is an **empty repositioning leg**.

It:

- consumes distance
- consumes time
- consumes fuel
- contributes to carbon emissions
- contributes to total operating cost

But it is NOT counted as a delivery leg.

---

## Step 3 — Delivery Leg

After reaching the assigned warehouse:

```text
Warehouse
    ↓
Stop 1
    ↓
Stop 2
    ↓
Stop 3
    ↓
...
    ↓
Final Stop
```

The ordered delivery stops must be determined by the optimization engine.

---

# 5. QIGA + QPSO OPTIMIZATION

Preserve the existing **QIGA + QPSO hybrid architecture**.

Do not replace the optimization engine with a simpler algorithm merely to make the UI work.

The restructuring changes the data flowing into the optimizer and how the result is displayed.

It does NOT remove the QIGA + QPSO architecture.

The optimizer must jointly determine:

### Discrete layer

Vehicle-to-parcel assignment.

### Continuous/timing layer

Stop ordering / timing optimization as implemented by the existing QPSO architecture.

The optimization objective should minimize overall company operating cost using:

- distance
- travel time
- fuel
- congestion
- SLA performance
- SLA violations for the SLA-Priority strategy

while respecting:

- vehicle capacity
- warehouse assignment
- route feasibility
- SLA constraints where applicable

---

# 6. TOMTOM TRAFFIC

Preserve the existing TomTom traffic integration.

Live TomTom traffic must feed into the cost function.

Traffic information must influence:

1. initial optimization
2. travel-time estimates
3. simulated arrival predictions

Do not fake the TomTom integration if an existing working integration is already present.

If API fallback/mock data is necessary for development or demo reliability, clearly separate:

```text
LIVE TOMTOM DATA
```

from:

```text
DEMO/FALLBACK TRAFFIC DATA
```

Do not falsely label fallback data as live traffic.

---

# 7. ACTIVE DASHBOARD

## Purpose

The Active Dashboard is the **main demo screen**.

It shows the live simulated operation of the fleet.

This should be the most visually important screen in the application.

---

## 7.1 ACTIVE DASHBOARD UI DESIGN

Use **Reference Image 1** as the primary visual reference.

The design language must be:

- dark charcoal
- premium
- restrained
- technical
- clean
- spacious
- map-centric
- minimal
- professional

### Background

Use a very dark **charcoal/near-black** background.

Avoid excessive blue/purple background tinting.

The main background should feel closer to:

```text
charcoal / graphite / black
```

than:

```text
neon blue / purple
```

---

## 7.2 COLOR SYSTEM

Use a restrained color system.

### Primary UI

- charcoal / graphite
- near-black
- dark gray
- light gray
- white

### Functional accents

Use muted:

- green → healthy/live/success
- blue → informational/selected state
- amber → warning/moderate traffic
- red → critical/SLA violation/high traffic

### IMPORTANT COLOR RULE

Colors must communicate meaning.

Do NOT use a different bright color for every component simply to make the UI look "modern."

Avoid:

- excessive neon
- purple glow
- blue glow
- rainbow cards
- gradient-heavy panels
- glowing borders everywhere
- brightly colored pills for ordinary information

The interface should feel **subtle and expensive**, not flashy.

---

## 7.3 ACTIVE DASHBOARD LAYOUT

Follow this general structure from Reference Image 1:

```text
┌───────────────────────────────────────────────────────────────┐
│ ABRAXAS     Pune Operations       Day / Time / Traffic       │
├────────────┬──────────────────────────────────────┬───────────┤
│            │                                      │           │
│ Navigation │                                      │ Fleet     │
│            │                                      │ Status    │
│ Active     │             LARGE MAP                │           │
│ Comparison │                                      │ Deliveries│
│ Analysis   │                                      │ SLA       │
│            │                                      │ Next Stops│
│            │                                      │           │
├────────────┴──────────────────────────────────────┴───────────┤
│ Distance │ Fuel │ Time │ Carbon │ Deliveries Completed       │
└───────────────────────────────────────────────────────────────┘
```

The map should remain the dominant element.

---

## 7.4 ACTIVE DASHBOARD HEADER

Include:

```text
ABRAXAS
Autonomous Logistics Intelligence

Pune Operations

Day XX / Demo

Simulation Time

60×
```

and a restrained traffic indicator:

```text
● TomTom Traffic
  Live
```

Simulation controls should include:

- pause
- resume
- simulation progress
- current simulated time
- simulation speed

---

## 7.5 ACTIVE MAP

The map is the visual hero.

Use:

- Leaflet
- OSM
- existing TomTom traffic integration where applicable

The map must show:

### Layer 1 — Vehicles

10–12 moving vehicle markers.

### Layer 2 — Warehouses

Exactly 3 fixed warehouse markers.

### Layer 3 — Delivery locations

50–60 delivery points.

Vehicle routes must be displayed as distinct route polylines.

Routes must follow the actual road network.

Do NOT draw straight lines between coordinates.

---

## 7.6 MAP VISUAL DESIGN

The map itself should remain dark and subdued.

Routes should be visible without overwhelming the map.

Use a restrained route palette.

Traffic visualization:

```text
Low      → muted green
Moderate → muted amber
High     → muted red
```

Do not make every route glow.

Only use stronger emphasis for:

- selected vehicle
- active route
- critical traffic
- important SLA event

---

## 7.7 ACTIVE DASHBOARD RIGHT PANEL

Include concise operational information.

### Fleet Status

Example:

```text
11 / 11
Active Vehicles
```

with a restrained breakdown:

```text
En Route
Delivering
Returning
Idle
```

### Deliveries

Show:

```text
Total Parcels
Completed
Remaining
```

### SLA

Show:

```text
SLA Compliance
On Time
Late
Upcoming
```

A small donut/ring visualization is acceptable.

Do not make it oversized or overly decorative.

### Next Stop Events

A compact table:

```text
Vehicle | Next Stop | ETA
```

Only show the most relevant upcoming vehicles.

---

## 7.8 ACTIVE DASHBOARD BOTTOM KPI STRIP

Show:

- Total Distance
- Fuel Consumed
- Total Time
- Carbon Emissions
- Deliveries Completed

The KPI strip should be clean and horizontally aligned.

Avoid putting every possible metric here.

---

## 7.9 SIMULATION

Use:

```text
1 real-world minute = 60 simulated minutes
```

This must be a configurable constant.

Example:

```text
SIMULATION_SPEED_MULTIPLIER = 60
```

Do NOT hardcode `60` throughout the codebase.

A full simulated 10-hour working day should take approximately 10 real-world minutes.

---

# 8. COMPARISON DASHBOARD

## Purpose

This screen is the **decision-making screen**.

Use **Reference Image 2** as the primary visual reference.

The admin should be able to compare optimization strategies and decide which strategy to assign.

---

## 8.1 FOUR PRESETS

Keep all four:

### Balanced

Balances:

- SLA
- fuel
- distance

### Fuel

Primarily minimizes:

- fuel
- operating cost

### Shortest Distance

Primarily minimizes:

- total distance

### SLA-Priority

Primarily prioritizes:

- meeting narrow SLA windows

Even if this increases:

- fuel
- distance
- time

---

## 8.2 APPLES-TO-APPLES COMPARISON

Every preset must use exactly the same:

- delivery sheet
- warehouses
- vehicles
- vehicle capacities
- vehicle starting positions
- traffic snapshot/data basis

Only the optimization objective/weights should change.

This is essential for a credible comparison.

---

## 8.3 COMPARISON UI

Use four strategy cards across the top.

Each should show:

```text
Strategy

Distance
Fuel
Time
CO₂
SLA Compliance
```

Do not overload the cards.

The selected strategy should have a subtle border/highlight.

Avoid bright neon cards.

---

## 8.4 ROUTE PREVIEW

Below the strategy cards, show the route preview map.

The admin can switch between:

```text
Balanced
Fuel
Shortest Distance
SLA-Priority
```

The map updates to show that strategy's computed routes.

The map should follow the same visual language as Active Dashboard.

---

## 8.5 STRATEGY INSIGHTS

Include a concise insight section explaining trade-offs.

Example:

```text
SLA-Priority

+11% SLA compliance
+7% distance
+8% fuel
```

The values must be calculated from the actual comparison results.

Do not hardcode fake improvement numbers.

---

## 8.6 VEHICLE ASSIGNMENT TABLE

Show the selected strategy's assignments:

```text
Vehicle
Warehouse
Assigned Stops
Total Distance
Estimated Time
```

The table should be scrollable if necessary.

Do not cram 10–12 vehicles into an unreadable fixed-height component.

---

## 8.7 ASSIGN ACTION

Provide one clear primary action:

```text
Assign [Selected Strategy]
```

When clicked:

1. Lock the selected strategy.
2. Store its vehicle assignments.
3. Store its routes.
4. Store its metrics.
5. Make it the active plan.
6. Start the simulation.
7. Navigate/show the Active Dashboard.

No mixed-preset assignment.

The entire fleet must use the selected preset.

---

# 9. ANALYSIS DASHBOARD

## Purpose

The Analysis Dashboard is the **judge-facing storytelling screen**.

Use **Reference Image 3** as the primary visual reference.

It should answer:

> "Has the system actually improved fleet performance over time?"

---

## 9.1 TOP KPI SUMMARY

Show a concise historical summary:

- Total Deliveries
- Average SLA Compliance
- Total Distance
- Total Fuel Consumed
- Carbon Emissions

Where possible, show change versus the previous period/session.

Do not invent trends.

Calculate them from historical session data.

---

## 9.2 PERFORMANCE TRENDS

Provide a day-wise chart.

Possible metrics:

- SLA Compliance
- Fuel Consumption
- Distance
- CO₂

Allow the user to switch the metric rather than displaying four giant charts simultaneously.

The chart should remain visually clean.

---

## 9.3 PRESET PERFORMANCE COMPARISON

Provide a comparison visualization for:

```text
Balanced
Fuel
Shortest Distance
SLA-Priority
```

Compare relevant metrics such as:

- distance
- fuel
- SLA

Use a restrained chart style.

Avoid excessive colors.

Use consistent semantic colors across the entire application.

---

## 9.4 SESSION HISTORY

Show historical sessions in a clean table.

Minimum fields:

```text
Day / Session
Date
Preset Used
Parcels
Distance
Fuel
CO₂
SLA
Status
```

Pre-seed 2–3 historical sessions.

When a new session is assigned/run/completed, append it automatically.

---

## 9.5 KEY INSIGHTS

Provide a concise insight panel.

Examples:

```text
SLA compliance improved over recent sessions.

Fuel consumption decreased.

Average route distance decreased.

Carbon emissions decreased.
```

These statements must be generated from the actual historical data.

Do not create fictional improvements.

---

# 10. DATA FLOW BETWEEN THE THREE DASHBOARDS

This is extremely important.

The three dashboards must not behave like disconnected mock screens.

They must use the same underlying application state.

The flow should be:

```text
Delivery Sheet
      ↓
Vehicle Starting Positions
      ↓
Comparison Dashboard
      ↓
QIGA + QPSO
      ↓
4 Strategy Results
      ↓
Admin Selects Strategy
      ↓
ASSIGN
      ↓
Active Dashboard
      ↓
Simulation
      ↓
Session Metrics
      ↓
Analysis Dashboard
```

The selected plan must be the exact plan simulated on the Active Dashboard.

The metrics shown in Analysis must come from the actual session.

---

# 11. HISTORICAL SESSION CREATION

When a session is assigned and run:

Create a historical record containing at minimum:

```text
session_id
date
session_label
parcel_count
completed_parcels
preset_used
total_distance
fuel_consumed
total_time
carbon_emissions
sla_compliance
status
```

The Analysis Dashboard must consume this data.

Do not maintain separate fake datasets for the charts and actual application state.

---

# 12. UI DESIGN SYSTEM — APPLY TO ALL THREE DASHBOARDS

The three reference images must feel like **one application**.

## Background

Primary background:

```text
Dark charcoal / graphite / near-black
```

Avoid strong navy/purple backgrounds.

---

## Panels

Use:

- subtle dark-gray surfaces
- very thin borders
- restrained shadows
- modest corner radius

Avoid:

- giant floating cards
- excessive glassmorphism
- heavy gradients
- glowing edges

---

## Typography

Use a clean modern sans-serif.

Hierarchy should be obvious:

```text
Page Title
    ↓
Section Title
    ↓
Supporting Text
    ↓
Metric
    ↓
Metadata
```

Do not use too many font sizes.

---

## Spacing

Prefer generous whitespace.

Every component should have breathing room.

Do not attempt to fill every empty part of the screen.

**Empty space is intentional.**

---

## Icons

Use icons only where they improve comprehension.

Do not place an icon next to every piece of text.

---

## Borders

Use borders primarily to:

- separate sections
- define major panels
- establish hierarchy

Do not put a border around every tiny element.

---

## Status indicators

Use semantic colors consistently.

```text
Green → healthy / live / completed / on-time

Blue → selected / informational

Amber → warning / moderate traffic

Red → critical / late / SLA violation
```

---

# 13. IMPORTANT — AVOID AI-GENERATED DASHBOARD CLUTTER

Do NOT interpret this project as a generic "futuristic AI dashboard."

Specifically avoid:

- excessive glowing effects
- purple neon
- excessive blue neon
- rainbow UI
- excessive gradients
- giant rounded cards
- cards inside cards inside cards
- unnecessary badges
- unnecessary pills
- excessive iconography
- decorative graphs
- fake "AI" visual effects
- excessive animations
- excessive shadows
- overly saturated colors
- meaningless metrics
- information repeated in multiple places

The goal is:

> **Premium logistics operations software — not a flashy AI template.**

The UI should look like something a serious fleet operations company could actually use.

---

# 14. RESPONSIVENESS

The primary target is a desktop/laptop presentation screen.

Prioritize the desktop layout.

However:

- avoid fixed dimensions that break the UI
- use responsive grids
- ensure the map resizes correctly
- ensure tables can scroll
- avoid content clipping
- ensure the three dashboards maintain visual consistency

---

# 15. MAP PERFORMANCE

There may be:

- 50–60 delivery points
- 10–12 vehicles
- multiple route polylines
- traffic information

The map must remain performant.

Do not introduce unnecessary animation or rendering overhead.

Vehicle movement should update smoothly without constantly rebuilding the entire map.

---

# 16. DATA / ALGORITHM CONSTRAINTS

Vehicle capacity is a **hard constraint**.

No optimized solution may assign more parcels to a vehicle than its fixed capacity.

Each vehicle may serve only one warehouse per day.

SLA windows are:

- soft/scored under Balanced
- soft/scored under Fuel
- soft/scored under Shortest Distance
- **hard feasibility requirement under SLA-Priority**

The optimization engine must respect the existing QIGA + QPSO architecture.

---

# 17. DEMO RELIABILITY

This application is being demonstrated to judges.

Therefore prioritize:

- deterministic demo data
- reproducible routes
- reliable simulation
- predictable UI state
- fast dashboard loading
- graceful API failure handling
- clear loading states
- clear error states

Do not introduce unnecessary dependencies or architecture changes unless they are genuinely required.

If live APIs fail temporarily, the application should have a clearly identified fallback/demo mode rather than becoming unusable.

---

# 18. PHASED IMPLEMENTATION PLAN

Implement the project in the following exact order.

---

## PHASE 0 — AUDIT

Inspect the existing project.

Produce:

- architecture summary
- current modules
- current data model
- current routing flow
- current optimization flow
- current UI structure
- migration plan
- files to remove
- files to modify
- files to create

**STOP AND WAIT FOR APPROVAL.**

---

## PHASE 1 — DATA MODEL + DEMO DATA

Implement:

- 3 warehouses
- 10–12 vehicles
- fixed 4–7 capacities
- daily warehouse assignment
- daily starting positions
- 50–60 parcels/day
- strategically distributed Pune locations
- narrow SLA windows
- multiple demo days
- 2–3 historical analysis sessions

Verify capacity and data consistency.

**STOP AND WAIT FOR REVIEW.**

---

## PHASE 2 — ROUTING + SIMULATION PIPELINE

Implement/modify:

```text
Vehicle Start
     ↓
Road Snap
     ↓
Warehouse
     ↓
Optimized Delivery Stops
     ↓
Road-Snapped Route Geometry
     ↓
Traffic-Aware Cost
     ↓
Simulation
```

Implement configurable:

```text
SIMULATION_SPEED_MULTIPLIER = 60
```

Verify:

- repositioning leg is included in cost
- delivery leg is separate
- routes follow roads
- vehicle movement follows route geometry
- traffic affects timing/cost

**STOP AND WAIT FOR REVIEW.**

---

## PHASE 3 — APPLICATION SHELL + UI FOUNDATION

Before building individual dashboards:

Create the unified admin shell:

- dark charcoal theme
- left navigation
- top header
- typography
- spacing system
- cards/panels
- buttons
- tables
- status indicators
- chart styling
- map container styling

Navigation must contain exactly:

```text
Active Dashboard
Comparison Dashboard
Analysis Dashboard
```

Remove the old driver-facing navigation/workflows.

Use the three attached reference images as the visual benchmark.

**STOP AND WAIT FOR REVIEW.**

---

## PHASE 4 — ACTIVE DASHBOARD

Implement the complete Active Dashboard.

Map-first layout.

Include:

- live vehicles
- warehouses
- deliveries
- routes
- simulation controls
- simulation progress
- fleet status
- delivery status
- SLA status
- next stop events
- bottom KPI strip

Connect it to the actual assigned plan from Phase 2.

Do not use placeholder/mock UI data where real application data is available.

**STOP AND WAIT FOR REVIEW.**

---

## PHASE 5 — COMPARISON DASHBOARD

Implement:

- four presets
- apples-to-apples comparison
- strategy metrics
- route preview
- strategy insights
- vehicle assignment table
- strategy selection
- Assign button

Connect it to the real QIGA + QPSO engine.

The selected strategy must become the actual active plan.

**STOP AND WAIT FOR REVIEW.**

---

## PHASE 6 — ANALYSIS DASHBOARD

Implement:

- historical KPI cards
- performance trend chart
- preset comparison
- session history
- key insights

Connect it to actual historical session records.

No fake hardcoded trends.

**STOP AND WAIT FOR REVIEW.**

---

## PHASE 7 — FULL END-TO-END DEMO VALIDATION

Run the complete flow:

```text
Open Application
      ↓
Comparison Dashboard
      ↓
Select Day
      ↓
Run/Load Optimization
      ↓
Compare 4 Presets
      ↓
Select Preset
      ↓
Assign
      ↓
Active Dashboard
      ↓
Simulation Begins
      ↓
Vehicles Move
      ↓
Deliveries Complete
      ↓
Session Metrics Recorded
      ↓
Analysis Dashboard
      ↓
New Historical Session Appears
```

Verify that the data remains consistent throughout the entire flow.

Specifically verify:

- parcel counts
- vehicle assignments
- vehicle capacities
- warehouse assignments
- routes
- distance
- fuel
- time
- CO₂
- SLA compliance
- historical metrics

**STOP AND WAIT FOR FINAL REVIEW.**

---

# 19. DEFINITION OF DONE

The restructuring is complete only when:

### Architecture

- Driver panel removed
- Exactly three admin dashboards
- Shared data/state between dashboards

### Fleet

- 10–12 vehicles
- fixed 4–7 parcel capacity
- 3 warehouses
- one warehouse per vehicle per day
- fresh starting positions each day

### Deliveries

- 50–60 parcels/day
- strategically distributed Pune locations
- narrow SLA windows

### Optimization

- QIGA + QPSO preserved
- capacity constraints enforced
- warehouse constraints enforced
- SLA behavior implemented correctly
- four presets working
- same input conditions for fair comparison

### Routing

- road-snapped routes
- repositioning leg
- delivery leg
- TomTom traffic integration
- synthesized route-based vehicle movement

### Simulation

- 60× default speed
- configurable speed
- realistic route interpolation
- live metric updates

### Active Dashboard

- map-first
- clear fleet status
- delivery status
- SLA status
- next stops
- KPIs
- simulation controls

### Comparison Dashboard

- four strategy cards
- comparable metrics
- route preview
- assignments
- strategy selection
- Assign action

### Analysis Dashboard

- historical sessions
- trends
- preset comparison
- session table
- calculated insights

### UI

The final UI must visually resemble the attached references:

> **Dark charcoal + restrained accents + premium typography + generous spacing + clear hierarchy + map-centric operations design.**

It must NOT resemble the previous cluttered UI.

---

# 20. FINAL INSTRUCTION

Before every phase, inspect the current implementation and work with the existing architecture rather than blindly rewriting it.

Do not delete working functionality unless it is explicitly superseded by this specification.

Do not create duplicate systems for functionality that already exists.

Do not fabricate metrics when real calculations are available.

Do not fabricate API status.

Do not fabricate optimization results.

Do not fabricate historical trends.

And most importantly:

**DO NOT IMPLEMENT ALL PHASES AT ONCE.**

Complete one phase → report changes → show result → **WAIT FOR MY APPROVAL** → proceed to the next phase.

The three attached UI images are the visual reference for the final product and should be treated as a consistent design system across all three dashboards.
