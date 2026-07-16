# E2E Acceptance Validation Plan — PrismIQ

This acceptance test checklist outlines user journeys, edge-case scenarios, and visual assertions to verify the PrismIQ application.

---

## Core User Journeys

### 1. Authentication & Session Lifecycles
- [ ] **Registration Flow**: Create a new account under `/register`. Verify validation rules for missing fields and mismatched passwords.
- [ ] **Login Flow**: Sign in with registered credentials. Verify redirection to `/dashboard`.
- [ ] **Session Persistence**: Refresh the browser page. Confirm that the dashboard remains loaded (no redirects to `/login` occur).
- [ ] **Token Expiration Interceptor**: Simulate token expiration. Verify that the Axios interceptor catches `401` errors, refreshes tokens silently, and replays requests without session disruption.
- [ ] **Logout Flow**: Click the Log out button. Verify local storage tokens are cleared and the user is redirected to `/login`.

### 2. Dataset Workspaces Ingestion
- [ ] **Drag-and-Drop Ingestion**: Drop a CSV file into the importer area on `/datasets/import`. Specify a custom name.
- [ ] **Ingestion Validation**: Propose invalid formats (e.g. PNG files). Confirm that custom error bounds appear.
- [ ] **Details Redirect**: Verify successful ingestion redirects to `/datasets/:id/preview`.

### 3. Analytics Pipeline Slices
- [ ] **Preview Grid**: Check grid data displays correct headers, samples, and pagination controls.
- [ ] **Profiling Diagnostics**: Click "Trigger Data Profiling". Verify metrics cards (Quality Index, Duplicate rows, Missing cells) and schema column tables update correctly.
- [ ] **Smart Cleaning Wizards**: Configure cleaning rules. Preview deltas, apply changes, and confirm that the current workspace version is updated to Version 2.
- [ ] **Exploratory EDA**: Trigger EDA. Verify that the Pearson correlation matrix heatmap cell colors map to coefficient strengths dynamically.
- [ ] **AI Insights**: Trigger AI Insights. Verify observation listings display severity tags (HIGH/MEDIUM/LOW) and actionability percentages.

### 4. Compiling & Comparing
- [ ] **Reports Console**: Compile HTML, PDF, Excel sheet, and JSON formats. Confirm downloads open successfully.
- [ ] **Versions Comparison**: Select Version 1 and Version 2 in comparison panels. Verify offsets for duplicate counts, missing deltas, and columns are visual.
