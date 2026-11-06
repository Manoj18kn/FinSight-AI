var transactions = [];
var charts = {};

var demoDataset = [
  { id: 1, date: "2026-10-01", desc: "TCS Technology Salary", category: "Salary", type: "CR", amount: 82000, suspicious: false },
  { id: 2, date: "2026-10-03", desc: "Apartment Rent", category: "Rent", type: "DR", amount: 22000, suspicious: false },
  { id: 3, date: "2026-10-06", desc: "Supermarket Groceries", category: "Food & Groceries", type: "DR", amount: 4800, suspicious: false },
  { id: 4, date: "2026-10-10", desc: "Crypto P2P Outflow", category: "High Risk", type: "DR", amount: 25000, suspicious: true },
  { id: 5, date: "2026-10-14", desc: "Electricity Bill", category: "Utilities", type: "DR", amount: 3200, suspicious: false },
  { id: 6, date: "2026-10-18", desc: "Restaurant Dining", category: "Wants", type: "DR", amount: 4500, suspicious: false },
  { id: 7, date: "2026-10-24", desc: "Midnight POS Charge", category: "Suspicious", type: "DR", amount: 18500, suspicious: true },
  { id: 8, date: "2026-10-28", desc: "Mutual Fund SIP", category: "Savings", type: "DR", amount: 10000, suspicious: false },
  { id: 9, date: "2026-10-29", desc: "Freelance Consulting", category: "Salary", type: "CR", amount: 15000, suspicious: false }
];

function formatINR(val) {
  return "₹" + Math.round(val).toLocaleString("en-IN");
}

function runAnalysis() {
  var income = 0;
  var expense = 0;
  var fraudCount = 0;
  var crCount = 0;
  var drCount = 0;

  for (var i = 0; i < transactions.length; i++) {
    var tx = transactions[i];
    if (tx.type === "CR") {
      income += tx.amount;
      crCount++;
    } else {
      expense += tx.amount;
      drCount++;
    }
    if (tx.suspicious) {
      fraudCount++;
    }
  }

  var savings = Math.max(0, income - expense);
  var savingsRate = income > 0 ? savings / income : 0;
  var score = Math.round(savingsRate * 60) + (fraudCount === 0 ? 35 : Math.max(0, 35 - fraudCount * 15)) + 5;
  score = Math.min(Math.max(score, 20), 98);

  var kpiIncome = document.getElementById("kpiIncome");
  var kpiExpense = document.getElementById("kpiExpense");
  var kpiTxCredit = document.getElementById("kpiTxCredit");
  var kpiTxDebit = document.getElementById("kpiTxDebit");
  var kpiFraud = document.getElementById("kpiFraud");
  var kpiScore = document.getElementById("kpiScore");
  var kpiScoreLabel = document.getElementById("kpiScoreLabel");

  if (kpiIncome) kpiIncome.textContent = formatINR(income);
  if (kpiExpense) kpiExpense.textContent = formatINR(expense);
  if (kpiTxCredit) kpiTxCredit.textContent = crCount + " credits";
  if (kpiTxDebit) kpiTxDebit.textContent = drCount + " debits";
  if (kpiFraud) kpiFraud.textContent = fraudCount + " Detected";
  if (kpiScore) kpiScore.textContent = score + " / 100";
  if (kpiScoreLabel) kpiScoreLabel.textContent = score >= 80 ? "Prime Tier" : score >= 60 ? "Moderate" : "High Risk";

  renderTransactionTable(false);
  updateChartsSafe(income, expense);
  computeForecast(income, expense);
  computeBudget(income, expense);
  computeInvestment(income, expense);
}

function renderTransactionTable(filterFlagged) {
  var tbody = document.getElementById("transactionTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  var searchEl = document.getElementById("txSearch");
  var catEl = document.getElementById("txFilterCategory");
  var searchVal = searchEl ? searchEl.value.toLowerCase() : "";
  var categoryVal = catEl ? catEl.value : "all";

  var filtered = [];
  for (var i = 0; i < transactions.length; i++) {
    var t = transactions[i];
    var matchesSearch = t.desc.toLowerCase().indexOf(searchVal) !== -1 || t.category.toLowerCase().indexOf(searchVal) !== -1;
    var matchesCategory = categoryVal === "all" || t.category === categoryVal;
    var matchesFlagged = filterFlagged ? t.suspicious : true;
    if (matchesSearch && matchesCategory && matchesFlagged) {
      filtered.push(t);
    }
  }

  if (filtered.length === 0) {
    tbody.innerHTML = "<tr><td colspan='7' style='text-align:center; padding: 15px;'>No transactions found.</td></tr>";
    return;
  }

  for (var j = 0; j < filtered.length; j++) {
    (function(tx) {
      var tr = document.createElement("tr");
      var typeClass = tx.type === "CR" ? "badge-cr" : "badge-dr";
      var colorStyle = tx.type === "CR" ? "color: var(--accent-green);" : "color: var(--accent-red);";
      var sign = tx.type === "CR" ? "+" : "-";
      var badgeClass = tx.suspicious ? "badge-fraud" : "badge-normal";
      var badgeText = tx.suspicious ? "⚠ Flagged" : "Normal";

      tr.innerHTML = 
        "<td>" + tx.date + "</td>" +
        "<td><strong>" + tx.desc + "</strong></td>" +
        "<td>" + tx.category + "</td>" +
        "<td><span class='badge " + typeClass + "'>" + tx.type + "</span></td>" +
        "<td style='font-weight:600; " + colorStyle + "'>" + sign + formatINR(tx.amount) + "</td>" +
        "<td><span class='badge " + badgeClass + "'>" + badgeText + "</span></td>" +
        "<td><button type='button' class='btn btn-secondary' style='padding: 2px 6px; font-size: 0.7rem;'>Toggle</button></td>";

      var btn = tr.querySelector("button");
      btn.addEventListener("click", function() {
        tx.suspicious = !tx.suspicious;
        runAnalysis();
      });

      tbody.appendChild(tr);
    })(filtered[j]);
  }
}

function updateChartsSafe(income, expense) {
  if (typeof Chart === "undefined") return;

  var el1 = document.getElementById("cashflowChart");
  if (el1) {
    if (charts.cashflow) charts.cashflow.destroy();
    charts.cashflow = new Chart(el1.getContext("2d"), {
      type: "bar",
      data: {
        labels: ["Inflow", "Outflow", "Retained"],
        datasets: [{
          data: [income, expense, Math.max(0, income - expense)],
          backgroundColor: ["#10b981", "#ef4444", "#38bdf8"]
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });
  }

  var el2 = document.getElementById("categoryChart");
  if (el2) {
    var catMap = {};
    for (var i = 0; i < transactions.length; i++) {
      if (transactions[i].type === "DR") {
        var cat = transactions[i].category;
        catMap[cat] = (catMap[cat] || 0) + transactions[i].amount;
      }
    }

    if (charts.category) charts.category.destroy();
    charts.category = new Chart(el2.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: Object.keys(catMap),
        datasets: [{
          data: Object.values(catMap),
          backgroundColor: ["#38bdf8", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6"]
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } }
    });
  }
}

function computeForecast(income, expense) {
  var predictedOutflow = Math.round(expense * 1.05);
  var predictedSavings = Math.max(0, income - predictedOutflow);
  var runwayMonths = predictedOutflow > 0 ? (income / predictedOutflow).toFixed(1) : "0";

  var predOutflow = document.getElementById("predOutflow");
  var predSavings = document.getElementById("predSavings");
  var predRunway = document.getElementById("predRunway");

  if (predOutflow) predOutflow.textContent = formatINR(predictedOutflow);
  if (predSavings) predSavings.textContent = formatINR(predictedSavings);
  if (predRunway) predRunway.textContent = runwayMonths + " Months";

  var el3 = document.getElementById("predictionChart");
  if (el3 && typeof Chart !== "undefined") {
    if (charts.prediction) charts.prediction.destroy();
    charts.prediction = new Chart(el3.getContext("2d"), {
      type: "line",
      data: {
        labels: ["Current", "M+1", "M+2", "M+3"],
        datasets: [{
          label: "Predicted Burn",
          data: [expense, predictedOutflow, predictedOutflow * 1.03, predictedOutflow * 1.06],
          borderColor: "#f59e0b",
          fill: false
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }
}

function computeBudget(income, expense) {
  var needsCap = income * 0.50;
  var wantsCap = income * 0.30;
  var savingsTarget = income * 0.20;

  var actualNeeds = 0;
  var actualWants = 0;

  for (var i = 0; i < transactions.length; i++) {
    var t = transactions[i];
    if (t.type === "DR") {
      if (t.category === "Rent" || t.category === "Food & Groceries" || t.category === "Utilities") {
        actualNeeds += t.amount;
      } else {
        actualWants += t.amount;
      }
    }
  }

  var actualSavings = Math.max(0, income - expense);

  var budgetNeedsVal = document.getElementById("budgetNeedsVal");
  var budgetWantsVal = document.getElementById("budgetWantsVal");
  var budgetSavingsVal = document.getElementById("budgetSavingsVal");

  if (budgetNeedsVal) budgetNeedsVal.textContent = formatINR(actualNeeds) + " / " + formatINR(needsCap);
  if (budgetWantsVal) budgetWantsVal.textContent = formatINR(actualWants) + " / " + formatINR(wantsCap);
  if (budgetSavingsVal) budgetSavingsVal.textContent = formatINR(actualSavings) + " / " + formatINR(savingsTarget);

  var barNeeds = document.getElementById("barNeeds");
  var barWants = document.getElementById("barWants");
  var barSavings = document.getElementById("barSavings");

  if (barNeeds) barNeeds.style.width = Math.min(100, needsCap > 0 ? (actualNeeds / needsCap) * 100 : 0) + "%";
  if (barWants) barWants.style.width = Math.min(100, wantsCap > 0 ? (actualWants / wantsCap) * 100 : 0) + "%";
  if (barSavings) barSavings.style.width = Math.min(100, savingsTarget > 0 ? (actualSavings / savingsTarget) * 100 : 0) + "%";
}

function computeInvestment(income, expense) {
  var surplus = Math.max(0, income - expense);
  var investEmergency = document.getElementById("investEmergency");
  var investEquity = document.getElementById("investEquity");
  var investDebt = document.getElementById("investDebt");

  if (investEmergency) investEmergency.textContent = formatINR(surplus * 0.40);
  if (investEquity) investEquity.textContent = formatINR(surplus * 0.40);
  if (investDebt) investDebt.textContent = formatINR(surplus * 0.20);
}

// AI Assistant Chatbot (Pure English)
function postChatMessage(sender, text) {
  var box = document.getElementById("chatBox");
  if (!box) return;
  var bubble = document.createElement("div");
  bubble.className = "chat-bubble " + sender;
  bubble.textContent = text;
  box.appendChild(bubble);
  box.scrollTop = box.scrollHeight;
}

function processAssistantQuery(msg) {
  var q = msg.toLowerCase();
  var anomalies = [];
  for (var i = 0; i < transactions.length; i++) {
    if (transactions[i].suspicious) {
      anomalies.push(transactions[i]);
    }
  }

  // 1. Fraud & Suspicious Inquiries
  if (q.indexOf("fraud") !== -1 || q.indexOf("suspicious") !== -1 || q.indexOf("flag") !== -1 || q.indexOf("alert") !== -1) {
    if (anomalies.length === 0) {
      return "The statement is clean! No suspicious transactions or anomalies detected.";
    }
    var list = "";
    for (var j = 0; j < anomalies.length; j++) {
      list += "\n• " + anomalies[j].desc + " (" + formatINR(anomalies[j].amount) + ")";
    }
    return "Warning: Identified " + anomalies.length + " high-risk transactions:" + list + "\nRecommendation: Contact beneficiary or freeze cards immediately.";
  }

  // 2. Health Score Inquiries
  if (q.indexOf("score") !== -1 || q.indexOf("health") !== -1 || q.indexOf("rating") !== -1) {
    var scoreText = document.getElementById("kpiScore") ? document.getElementById("kpiScore").textContent : "N/A";
    var labelText = document.getElementById("kpiScoreLabel") ? document.getElementById("kpiScoreLabel").textContent : "Moderate";
    return "Your Financial Health Score is currently " + scoreText + " (" + labelText + "). Eliminating high-risk outflows and increasing your savings rate will raise it above 90.";
  }

  // 3. Budget & Savings Inquiries
  if (q.indexOf("budget") !== -1 || q.indexOf("save") !== -1 || q.indexOf("expense") !== -1 || q.indexOf("spend") !== -1) {
    return "Smart Budgeting Rule: Allocate 50% to essential Needs (Rent, Bills, Groceries), 30% to discretionary Wants, and save at least 20% in liquid reserves or mutual fund SIPs.";
  }

  // 4. Inflow & Income Inquiries
  if (q.indexOf("income") !== -1 || q.indexOf("salary") !== -1 || q.indexOf("credit") !== -1) {
    var incText = document.getElementById("kpiIncome") ? document.getElementById("kpiIncome").textContent : "0";
    return "Total verified inflow recorded for this cycle is " + incText + ". Your income displays steady recurring salary credits.";
  }

  // 5. Investment Advice
  if (q.indexOf("invest") !== -1 || q.indexOf("portfolio") !== -1 || q.indexOf("sip") !== -1) {
    return "Recommended Investment Strategy: Direct 40% into emergency liquid reserves, 40% into diversified equity index funds, and 20% into stable fixed income bonds.";
  }

  // Fallback response
  return "I am your AI Financial Underwriter. I can audit fraud flags, calculate budget velocity, and evaluate your health score. What would you like to review?";
}

document.addEventListener("DOMContentLoaded", function() {
  var navBtns = document.querySelectorAll(".nav-btn");
  for (var i = 0; i < navBtns.length; i++) {
    navBtns[i].addEventListener("click", function() {
      var allBtns = document.querySelectorAll(".nav-btn");
      for (var b = 0; b < allBtns.length; b++) {
        allBtns[b].classList.remove("active");
      }
      var allTabs = document.querySelectorAll(".tab-pane");
      for (var t = 0; t < allTabs.length; t++) {
        allTabs[t].classList.remove("active");
      }
      this.classList.add("active");
      var targetId = this.getAttribute("data-tab");
      var target = document.getElementById(targetId);
      if (target) {
        target.classList.add("active");
      }
    });
  }

  var btnLoad = document.getElementById("btnLoadSample");
  if (btnLoad) {
    btnLoad.addEventListener("click", function() {
      transactions = JSON.parse(JSON.stringify(demoDataset));
      runAnalysis();
      postChatMessage("bot", "Demo statement loaded and evaluated successfully!");
    });
  }

  var btnUploadTrigger = document.getElementById("btnUploadTrigger");
  var fileUpload = document.getElementById("fileUpload");
  if (btnUploadTrigger && fileUpload) {
    btnUploadTrigger.addEventListener("click", function() {
      fileUpload.click();
    });
    fileUpload.addEventListener("change", function(e) {
      var file = e.target.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function(evt) {
        var lines = evt.target.result.split("\n");
        var list = [];
        for (var l = 1; l < lines.length; l++) {
          var row = lines[l].trim().split(",");
          if (row.length >= 5) {
            list.push({
              id: l,
              date: row[0].trim(),
              desc: row[1].trim(),
              category: row[2].trim(),
              type: row[3].trim().toUpperCase(),
              amount: parseFloat(row[4].trim()) || 0,
              suspicious: row[5] ? row[5].trim().toLowerCase() === "true" : false
            });
          }
        }
        if (list.length > 0) {
          transactions = list;
          runAnalysis();
          postChatMessage("bot", "CSV parsed successfully: " + list.length + " transactions imported.");
        }
      };
      reader.readAsText(file);
    });
  }

  var btnExport = document.getElementById("btnExportReport");
  if (btnExport) {
    btnExport.addEventListener("click", function() {
      window.print();
    });
  }

  var txSearch = document.getElementById("txSearch");
  if (txSearch) {
    txSearch.addEventListener("input", function() {
      renderTransactionTable(false);
    });
  }

  var txFilterCategory = document.getElementById("txFilterCategory");
  if (txFilterCategory) {
    txFilterCategory.addEventListener("change", function() {
      renderTransactionTable(false);
    });
  }

  var flagOnly = false;
  var btnFilterFraudOnly = document.getElementById("btnFilterFraudOnly");
  if (btnFilterFraudOnly) {
    btnFilterFraudOnly.addEventListener("click", function() {
      flagOnly = !flagOnly;
      this.classList.toggle("btn-primary", flagOnly);
      renderTransactionTable(flagOnly);
    });
  }

  var btnSendChat = document.getElementById("btnSendChat");
  var chatInput = document.getElementById("chatInput");
  if (btnSendChat && chatInput) {
    var handleSend = function() {
      var val = chatInput.value.trim();
      if (!val) return;
      postChatMessage("user", val);
      chatInput.value = "";
      setTimeout(function() {
        var reply = processAssistantQuery(val);
        postChatMessage("bot", reply);
      }, 300);
    };

    btnSendChat.addEventListener("click", handleSend);
    chatInput.addEventListener("keydown", function(e) {
      if (e.key === "Enter") handleSend();
    });
  }

  transactions = JSON.parse(JSON.stringify(demoDataset));
  runAnalysis();
});