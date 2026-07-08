/*

Reliability Simulator

Part 1

- DOM references
- Utilities
- Form serialization
- Validation
- API client
- Loading state
- Error handling

Part 2 implements:

- Statistics rendering
- Circuit breaker rendering
- Trace rendering
- Event listeners

*/

"use strict";

// 
// Configuration
// 

const API_URL = "/simulate";

// 
// DOM References
// 

const form =
    document.getElementById("simulation-form");

const runButton =
    document.getElementById("run-button");

const resetButton =
    document.getElementById("reset-button");

const resultsSection =
    document.getElementById("results-section");

const loading =
    document.getElementById("loading");

const errorBox =
    document.getElementById("error-message");

const failureSlider =
    document.getElementById("failure-rate");

const failureValue =
    document.getElementById("failure-rate-value");

// Statistics

const successRate =
    document.getElementById("success-rate");

const failureRate =
    document.getElementById("failure-rate-result");

const totalRequests =
    document.getElementById("total-requests");

const retryCount =
    document.getElementById("retry-count");

const circuitOpens =
    document.getElementById("circuit-opens");

const averageLatency =
    document.getElementById("average-latency");

// Tables

const breakerTable =
    document.getElementById("breaker-table");

const traceTable =
    document.getElementById("trace-table");

// 
// Utility
// 

function show(element) {

    element.classList.remove("hidden");

}

function hide(element) {

    element.classList.add("hidden");

}

function clearChildren(element) {

    while (element.firstChild) {

        element.removeChild(
            element.firstChild
        );

    }

}

function formatPercent(value) {

    return `${(value * 100).toFixed(1)}%`;

}

function formatLatency(value) {

    return `${Number(value).toFixed(2)} ms`;

}

// 
// Loading
// 

function setLoading(isLoading) {

    if (isLoading) {

        show(resultsSection);

        show(loading);

        hide(errorBox);

        runButton.disabled = true;

        runButton.textContent =
            "Running...";

        return;

    }

    hide(loading);

    runButton.disabled = false;

    runButton.textContent =
        "Run Simulation";

}

// 
// Errors
// 

function showError(message) {

    show(resultsSection);

    errorBox.textContent = message;

    show(errorBox);

}

function clearError() {

    errorBox.textContent = "";

    hide(errorBox);

}

// 
// Form
// 

function selectedServices() {

    return Array.from(
        document.getElementById("services")
            .selectedOptions
    ).map(option => option.value);

}

function buildRequest() {

    return {

        services:
            selectedServices(),

        iterations:
            Number(
                document.getElementById(
                    "iterations"
                ).value
            ),

        failure_rate:
            Number(
                failureSlider.value
            ) / 100,

        retry_attempts:
            Number(
                document.getElementById(
                    "retry-attempts"
                ).value
            ),

        breaker_threshold:
            Number(
                document.getElementById(
                    "breaker-threshold"
                ).value
            ),

        latency_ms:
            Number(
                document.getElementById(
                    "latency"
                ).value
            ),

        random_seed:
            Number(
                document.getElementById(
                    "random-seed"
                ).value
            )

    };

}

// 
// Validation
// 

function validate(request) {

    if (
        request.services.length === 0
    ) {

        throw new Error(
            "Select at least one service."
        );

    }

    if (
        request.iterations <= 0
    ) {

        throw new Error(
            "Iterations must be greater than zero."
        );

    }

    if (
        request.failure_rate < 0 ||
        request.failure_rate > 1
    ) {

        throw new Error(
            "Failure rate is invalid."
        );

    }

}

// 
// API
// 

async function runSimulation(request) {

    const response =
        await fetch(API_URL, {

            method: "POST",

            headers: {

                "Content-Type":
                    "application/json"

            },

            body:
                JSON.stringify(request)

        });

    if (!response.ok) {

        let message =
            "Simulation failed.";

        try {

            const error =
                await response.json();

            message =
                error.detail || message;

        } catch (_) {}

        throw new Error(message);

    }

    return response.json();

}

// 
// Controller
// 

async function submitSimulation(event) {

    event.preventDefault();

    clearError();

    let request;

    try {

        request =
            buildRequest();

        validate(request);

    } catch (error) {

        showError(error.message);

        return;

    }

    try {

        setLoading(true);

        const result =
            await runSimulation(
                request
            );

        renderStatistics(result);
renderBreakers(result);
renderTraces(result);

    } catch (error) {

        showError(
            error.message
        );

    } finally {

        setLoading(false);

    }

}


// 
// Rendering
// 

function renderStatistics(result) {

    const stats = result.statistics;

    successRate.textContent =
        formatPercent(stats.success_rate);

    failureRate.textContent =
        formatPercent(stats.failure_rate);

    totalRequests.textContent =
        stats.total_requests;

    retryCount.textContent =
        stats.retries;

    circuitOpens.textContent =
        stats.circuit_opens;

    averageLatency.textContent =
        formatLatency(
            stats.average_latency_ms
        );

    show(resultsSection);
}

// ----------------------------------------------------------

function stateClass(state) {

    switch (state) {

        case "closed":
            return "status-success";

        case "half_open":
            return "status-warning";

        case "open":
            return "status-danger";

        default:
            return "";
    }

}

// ----------------------------------------------------------

function renderBreakers(result) {

    clearChildren(
        breakerTable
    );

    for (const breaker of result.circuit_breakers) {

        const row =
            document.createElement("tr");

        row.innerHTML = `
            <td>${breaker.service}</td>
            <td class="${stateClass(
                breaker.state
            )}">
                ${breaker.state}
            </td>
            <td>${breaker.successful_calls}</td>
            <td>${breaker.failed_calls}</td>
            <td>${breaker.consecutive_failures}</td>
        `;

        breakerTable.appendChild(
            row
        );

    }

}

// ----------------------------------------------------------

function renderTraces(result) {

    clearChildren(
        traceTable
    );

    for (const trace of result.traces) {

        const row =
            document.createElement("tr");

        const status =
            trace.success
                ? "Success"
                : "Failure";

        const statusCss =
            trace.success
                ? "status-success"
                : "status-danger";

        row.innerHTML = `
            <td>${trace.iteration}</td>
            <td>${trace.service}</td>

            <td class="${statusCss}">
                ${status}
            </td>

            <td>
                ${formatLatency(
                    trace.latency_ms
                )}
            </td>

            <td>
                ${trace.retries}
            </td>

            <td class="${stateClass(
                trace.circuit_state
            )}">
                ${trace.circuit_state}
            </td>

            <td>
                ${trace.failure}
            </td>

            <td>
                ${trace.message}
            </td>
        `;

        traceTable.appendChild(
            row
        );

    }

}

// 
// Reset
// 

function resetResults() {

    clearChildren(
        breakerTable
    );

    clearChildren(
        traceTable
    );

    successRate.textContent = "—";
    failureRate.textContent = "—";
    totalRequests.textContent = "—";
    retryCount.textContent = "—";
    circuitOpens.textContent = "—";
    averageLatency.textContent = "—";

    hide(resultsSection);

    clearError();

}

// 
// Slider
// 

failureSlider.addEventListener(
    "input",
    () => {

        failureValue.textContent =
            `${failureSlider.value}%`;

    }
);

// 
// Form Events
// 

form.addEventListener(
    "submit",
    submitSimulation
);

resetButton.addEventListener(
    "click",
    () => {

        resetResults();

    }
);

// 
// Initialization
// 

document.addEventListener(
    "DOMContentLoaded",
    () => {

        failureValue.textContent =
            `${failureSlider.value}%`;

        resetResults();

        console.log(
            "Reliability Simulator initialized."
        );

    }
);