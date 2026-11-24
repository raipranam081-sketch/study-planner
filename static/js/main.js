/**
 * Student Study Planner with Random Forest Recommendation
 * Frontend Application Scripts
 */

document.addEventListener("DOMContentLoaded", () => {
    initSidebarToggle();
    initModals();
    initTaskToggles();
    initPlannerToggles();
    initStudyTimer();
    initProgressCharts();
});

/* -------------------------------------------------------------
 * 1. Mobile Sidebar Toggle
 * ------------------------------------------------------------- */
function initSidebarToggle() {
    const toggleBtn = document.getElementById("mobileToggle");
    const sidebar = document.getElementById("sidebar");

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener("click", (e) => {
            if (window.innerWidth <= 768 && sidebar.classList.contains("open")) {
                if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                    sidebar.classList.remove("open");
                }
            }
        });
    }
}

/* -------------------------------------------------------------
 * 2. Modal Utilities
 * ------------------------------------------------------------- */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add("active");
        document.body.style.overflow = "hidden";
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove("active");
        document.body.style.overflow = "";
    }
}

function initModals() {
    // Close modal when clicking backdrop
    document.querySelectorAll(".modal-overlay").forEach((modal) => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });

    // Close on ESC key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll(".modal-overlay.active").forEach((m) => {
                closeModal(m.id);
            });
        }
    });
}

/* -------------------------------------------------------------
 * 3. Task AJAX Toggle
 * ------------------------------------------------------------- */
function initTaskToggles() {
    const checkboxes = document.querySelectorAll(".task-toggle-checkbox");
    checkboxes.forEach((cb) => {
        cb.addEventListener("change", async (e) => {
            const taskId = cb.dataset.taskId;
            const taskRow = document.getElementById(`task-row-${taskId}`);

            try {
                const response = await fetch(`/tasks/${taskId}/toggle`, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Content-Type": "application/json"
                    }
                });

                const data = await response.json();
                if (data.success) {
                    if (taskRow) {
                        const statusBadge = taskRow.querySelector(".task-status-badge");
                        const titleEl = taskRow.querySelector(".task-title");

                        if (data.new_status === "Completed") {
                            taskRow.classList.add("task-done");
                            if (statusBadge) {
                                statusBadge.className = "badge badge-success task-status-badge";
                                statusBadge.textContent = "Completed";
                            }
                            if (titleEl) titleEl.style.textDecoration = "line-through";
                        } else {
                            taskRow.classList.remove("task-done");
                            if (statusBadge) {
                                statusBadge.className = "badge badge-warning task-status-badge";
                                statusBadge.textContent = "Pending";
                            }
                            if (titleEl) titleEl.style.textDecoration = "none";
                        }
                    }
                }
            } catch (err) {
                console.error("Error toggling task:", err);
            }
        });
    });
}

/* -------------------------------------------------------------
 * 4. Weekly Planner Session AJAX Toggle
 * ------------------------------------------------------------- */
function initPlannerToggles() {
    const sessionCheckboxes = document.querySelectorAll(".planner-session-toggle");
    sessionCheckboxes.forEach((cb) => {
        cb.addEventListener("change", async (e) => {
            const sessionId = cb.dataset.sessionId;
            const card = document.getElementById(`session-card-${sessionId}`);

            try {
                const response = await fetch(`/planner/session/${sessionId}/toggle`, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Content-Type": "application/json"
                    }
                });

                const data = await response.json();
                if (data.success && card) {
                    if (data.completed) {
                        card.classList.add("is-completed");
                    } else {
                        card.classList.remove("is-completed");
                    }
                }
            } catch (err) {
                console.error("Error toggling planner session:", err);
            }
        });
    });
}

/* -------------------------------------------------------------
 * 5. Interactive Study Stopwatch / Timer
 * ------------------------------------------------------------- */
let timerInterval = null;
let secondsElapsed = 0;
let isTimerRunning = false;

function initStudyTimer() {
    const display = document.getElementById("stopwatchDisplay");
    const startBtn = document.getElementById("timerStartBtn");
    const pauseBtn = document.getElementById("timerPauseBtn");
    const resetBtn = document.getElementById("timerResetBtn");
    const syncDurationInput = document.getElementById("timerSyncDuration");

    if (!display || !startBtn) return;

    function formatTime(totalSeconds) {
        const hrs = Math.floor(totalSeconds / 3600);
        const mins = Math.floor((totalSeconds % 3600) / 60);
        const secs = totalSeconds % 60;
        return (
            String(hrs).padStart(2, "0") + ":" +
            String(mins).padStart(2, "0") + ":" +
            String(secs).padStart(2, "0")
        );
    }

    startBtn.addEventListener("click", () => {
        if (!isTimerRunning) {
            isTimerRunning = true;
            startBtn.style.display = "none";
            pauseBtn.style.display = "inline-flex";

            timerInterval = setInterval(() => {
                secondsElapsed++;
                display.textContent = formatTime(secondsElapsed);

                // Auto-sync into duration form (in minutes, min 1)
                if (syncDurationInput) {
                    const elapsedMins = Math.max(1, Math.round(secondsElapsed / 60));
                    syncDurationInput.value = elapsedMins;
                }
            }, 1000);
        }
    });

    pauseBtn.addEventListener("click", () => {
        if (isTimerRunning) {
            clearInterval(timerInterval);
            isTimerRunning = false;
            startBtn.style.display = "inline-flex";
            pauseBtn.style.display = "none";
        }
    });

    resetBtn.addEventListener("click", () => {
        clearInterval(timerInterval);
        isTimerRunning = false;
        secondsElapsed = 0;
        display.textContent = "00:00:00";
        startBtn.style.display = "inline-flex";
        pauseBtn.style.display = "none";
    });
}

/* -------------------------------------------------------------
 * 6. Dynamic Chart.js Analytics for Progress Page
 * ------------------------------------------------------------- */
async function initProgressCharts() {
    const chartSubCanvas = document.getElementById("chartSubjectHours");
    const chartWeeklyCanvas = document.getElementById("chartWeeklyTrend");
    const chartTaskCanvas = document.getElementById("chartTaskBreakdown");
    const chartSyllabusCanvas = document.getElementById("chartSyllabusProgress");

    if (!chartSubCanvas && !chartWeeklyCanvas) return;

    try {
        const response = await fetch("/api/progress_data");
        const data = await response.json();

        // 1. Subject Hours Doughnut Chart
        if (chartSubCanvas) {
            new Chart(chartSubCanvas, {
                type: "doughnut",
                data: {
                    labels: data.subject_distribution.labels.length > 0 ? data.subject_distribution.labels : ["No Data"],
                    datasets: [{
                        data: data.subject_distribution.values.length > 0 ? data.subject_distribution.values : [1],
                        backgroundColor: [
                            "#4F46E5", "#7C3AED", "#2563EB", "#06B6D4", "#10B981", "#F59E0B", "#EF4444"
                        ],
                        borderWidth: 2,
                        borderColor: "#FFFFFF"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom" }
                    }
                }
            });
        }

        // 2. Weekly Trend Bar Chart
        if (chartWeeklyCanvas) {
            new Chart(chartWeeklyCanvas, {
                type: "bar",
                data: {
                    labels: data.weekly_trend.labels,
                    datasets: [{
                        label: "Hours Studied",
                        data: data.weekly_trend.values,
                        backgroundColor: "rgba(79, 70, 229, 0.85)",
                        borderColor: "#4F46E5",
                        borderRadius: 8,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { callback: (val) => val + "h" }
                        }
                    }
                }
            });
        }

        // 3. Task Status Breakdown
        if (chartTaskCanvas) {
            new Chart(chartTaskCanvas, {
                type: "pie",
                data: {
                    labels: data.task_breakdown.labels,
                    datasets: [{
                        data: data.task_breakdown.values,
                        backgroundColor: ["#10B981", "#F59E0B"],
                        borderWidth: 2,
                        borderColor: "#FFFFFF"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom" }
                    }
                }
            });
        }

        // 4. Syllabus Progress Comparison
        if (chartSyllabusCanvas) {
            new Chart(chartSyllabusCanvas, {
                type: "bar",
                data: {
                    labels: data.syllabus_progress.labels,
                    datasets: [{
                        label: "Syllabus Completed (%)",
                        data: data.syllabus_progress.values,
                        backgroundColor: "rgba(124, 58, 237, 0.8)",
                        borderColor: "#7C3AED",
                        borderRadius: 6,
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { callback: (val) => val + "%" }
                        }
                    }
                }
            });
        }
    } catch (err) {
        console.error("Error loading progress charts:", err);
    }
}
