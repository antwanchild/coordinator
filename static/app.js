const TIME_VALUES = ['11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'];
const TIME_LABELS = ['11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM', '1:00 PM', '1:30 PM', '2:00 PM', '2:30 PM', '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM'];
const AM_TIMES = ['11:00', '11:30', '12:00', '12:30', '13:00'];
const PM_TIMES = ['14:00', '14:30', '15:00', '15:30', '16:00'];
const ROOM_TIMES = ['11:00', '11:30', '12:00', '12:30', '13:00', '14:00', '14:30', '15:00', '15:30', '16:00'];
const APP_VERSION = document.body.dataset.appVersion || 'dev';

let people = [];
let isPM = false;
let sidebarOpen = true;
let isLightMode = false;
let autoRefresh = false;
let currentAccent = localStorage.getItem('accent') || 'lime';
let currentPreviewUrl = null;

const roomData = {};
ROOM_TIMES.forEach(timeValue => {
  roomData[timeValue] = { off: '', b: '', s: '' };
});

const elements = {
  accentSelect: document.getElementById('accentSelect'),
  app: document.getElementById('app'),
  autoRefreshBtn: document.getElementById('autoRefreshBtn'),
  badgeAM: document.getElementById('badge-AM'),
  badgePM: document.getElementById('badge-PM'),
  buildBtn: document.getElementById('buildBtn'),
  clearNamesBtn: document.getElementById('clearNamesBtn'),
  copyCsvBtn: document.getElementById('copyCsvBtn'),
  csvInput: document.getElementById('csvInput'),
  exportBtn: document.getElementById('exportBtn'),
  headerStatus: document.getElementById('headerStatus'),
  helpBtn: document.getElementById('helpBtn'),
  helpCloseBtn: document.getElementById('helpCloseBtn'),
  helpModal: document.getElementById('helpModal'),
  importPasteBtn: document.getElementById('importPasteBtn'),
  nameInput: document.getElementById('nameInput'),
  nameList: document.getElementById('nameList'),
  pasteInput: document.getElementById('pasteInput'),
  peopleCount: document.getElementById('peopleCount'),
  previewArea: document.getElementById('previewArea'),
  previewTitle: document.getElementById('previewTitle'),
  sheetTabs: document.querySelectorAll('.sheet-tab'),
  inputTabs: document.querySelectorAll('.input-tab'),
  skippedCsv: document.getElementById('skipped-csv'),
  skippedPaste: document.getElementById('skipped-paste'),
  spinner: document.getElementById('spinner'),
  themeBtn: document.getElementById('themeBtn'),
  timeEnd: document.getElementById('timeEnd'),
  timeStart: document.getElementById('timeStart'),
  tipPopup: document.getElementById('tip-popup'),
  toast: document.getElementById('toast'),
  toggleBtn: document.getElementById('toggleBtn'),
};

init();

function init() {
  populateTimeDropdowns();
  restoreTheme();
  setAccent(currentAccent, false);
  bindEvents();
  wireTooltips();
  renderNameList();
}

function bindEvents() {
  elements.accentSelect.addEventListener('change', event => setAccent(event.target.value));
  elements.helpBtn.addEventListener('click', toggleHelp);
  elements.helpCloseBtn.addEventListener('click', toggleHelp);
  elements.themeBtn.addEventListener('click', toggleTheme);
  elements.toggleBtn.addEventListener('click', toggleSidebar);
  elements.buildBtn.addEventListener('click', build);
  elements.autoRefreshBtn.addEventListener('click', toggleAutoRefresh);
  elements.exportBtn.addEventListener('click', doExport);
  elements.addNameBtn = document.getElementById('addNameBtn');
  elements.addNameBtn.addEventListener('click', addName);
  elements.clearNamesBtn.addEventListener('click', clearNames);
  elements.copyCsvBtn.addEventListener('click', copyNamesAsCSV);
  elements.importPasteBtn.addEventListener('click', importPaste);
  elements.csvInput.addEventListener('change', event => handleCSV(event.target));
  elements.nameInput.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      addName();
    }
  });
  elements.nameList.addEventListener('click', handleNameListClick);
  elements.helpModal.addEventListener('click', event => {
    if (event.target === elements.helpModal) {
      toggleHelp();
    }
  });

  elements.sheetTabs.forEach(sheetTab => {
    sheetTab.addEventListener('click', () => selectSheet(sheetTab.dataset.sheet === 'PM'));
  });
  elements.inputTabs.forEach(inputTab => {
    inputTab.addEventListener('click', () => switchTab(inputTab.dataset.tab));
  });

  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
      event.preventDefault();
      build();
    }
    if (event.key === 'Escape') {
      elements.helpModal.classList.remove('show');
    }
  });
}

function wireTooltips() {
  document.querySelectorAll('.tip-icon').forEach(icon => {
    const nextElement = icon.nextElementSibling;
    const text = nextElement ? nextElement.textContent : '';
    if (!text) {
      return;
    }

    icon.addEventListener('mouseenter', () => {
      elements.tipPopup.textContent = text;
      elements.tipPopup.style.display = 'block';
      const rect = icon.getBoundingClientRect();
      let left = rect.left;
      const top = rect.bottom + 6;
      if (left + 260 > window.innerWidth - 10) {
        left = window.innerWidth - 270;
      }
      elements.tipPopup.style.left = `${left}px`;
      elements.tipPopup.style.top = `${top}px`;
    });

    icon.addEventListener('mouseleave', () => {
      elements.tipPopup.style.display = 'none';
    });
  });
}

function populateTimeDropdowns() {
  [elements.timeStart, elements.timeEnd].forEach(select => {
    select.innerHTML = TIME_VALUES.map((timeValue, index) => (
      `<option value="${timeValue}">${TIME_LABELS[index]}</option>`
    )).join('');
  });
  elements.timeEnd.value = '11:30';
}

function restoreTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    isLightMode = true;
    document.body.classList.add('light');
    elements.themeBtn.textContent = '🌙';
    elements.themeBtn.title = 'Switch to dark mode';
  }
}

function toggleTheme() {
  isLightMode = !isLightMode;
  document.body.classList.toggle('light', isLightMode);
  elements.themeBtn.textContent = isLightMode ? '🌙' : '☀️';
  elements.themeBtn.title = isLightMode ? 'Switch to dark mode' : 'Switch to light mode';
  localStorage.setItem('theme', isLightMode ? 'light' : 'dark');
}

function setAccent(accent, save = true) {
  document.body.classList.remove(
    'accent-lime', 'accent-blue', 'accent-purple', 'accent-green', 'accent-red',
    'accent-cyan', 'accent-orange', 'accent-pink', 'accent-teal'
  );
  document.body.classList.add(`accent-${accent}`);
  currentAccent = accent;
  elements.accentSelect.value = accent;
  if (save) {
    localStorage.setItem('accent', accent);
  }
}

function toggleSidebar() {
  sidebarOpen = !sidebarOpen;
  elements.app.classList.toggle('collapsed', !sidebarOpen);
  elements.toggleBtn.innerHTML = sidebarOpen ? '&#8249;' : '&#8250;';
  elements.toggleBtn.title = sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar';
  elements.toggleBtn.style.left = sidebarOpen ? '287px' : '-13px';
  elements.toggleBtn.classList.toggle('collapsed', !sidebarOpen);
}

function toggleHelp() {
  elements.helpModal.classList.toggle('show');
}

function toggleAutoRefresh() {
  autoRefresh = !autoRefresh;
  elements.autoRefreshBtn.classList.toggle('active', autoRefresh);
  elements.autoRefreshBtn.title = autoRefresh ? 'Auto-refresh on' : 'Auto-refresh off';
  toast(autoRefresh ? 'Auto-refresh on' : 'Auto-refresh off');
}

function maybeRefresh() {
  if (autoRefresh && !elements.previewArea.classList.contains('preview-empty')) {
    build();
  }
}

function selectSheet(showPmSheet) {
  isPM = showPmSheet;
  elements.sheetTabs.forEach(sheetTab => {
    sheetTab.classList.toggle('active', sheetTab.dataset.sheet === (showPmSheet ? 'PM' : 'AM'));
  });
  elements.headerStatus.innerHTML = `${showPmSheet ? 'PM Sheet' : 'AM Sheet'}&nbsp;&middot;&nbsp; v${APP_VERSION}`;
  elements.previewTitle.textContent = `${showPmSheet ? 'P.M.' : 'A.M.'} - ${showPmSheet ? 'PM' : 'AM'}`;
  if (!elements.previewArea.classList.contains('preview-empty')) {
    build();
  }
}

function switchTab(tabName) {
  ['manual', 'csv', 'paste'].forEach(tab => {
    document.getElementById(`tab-${tab}`).classList.toggle('active', tab === tabName);
    document.getElementById(`panel-${tab}`).style.display = tab === tabName ? 'block' : 'none';
  });
}

function toMinutes(timeStr) {
  if (!timeStr) {
    return 0;
  }
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
}

function personOnSheet(person, showPmSheet) {
  const sheetTimes = showPmSheet ? PM_TIMES : AM_TIMES;
  const domainStart = toMinutes(sheetTimes[0]);
  const domainEnd = toMinutes(sheetTimes[sheetTimes.length - 1]) + 30;
  return person.ranges.some(range => toMinutes(range.start) < domainEnd && toMinutes(range.end) > domainStart);
}

function countOnSheet(showPmSheet) {
  return people.filter(person => personOnSheet(person, showPmSheet)).length;
}

function formatTime12(timeValue) {
  if (!timeValue) {
    return '';
  }
  const [hours, minutes] = timeValue.split(':').map(Number);
  const period = hours >= 12 ? 'PM' : 'AM';
  const hour12 = hours > 12 ? hours - 12 : (hours === 0 ? 12 : hours);
  return `${hour12}:${minutes < 10 ? `0${minutes}` : minutes} ${period}`;
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function todayFilename() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `schedule-${year}-${month}-${day}.xlsx`;
}

function addName() {
  const rawInput = elements.nameInput.value.trim();
  if (!rawInput) {
    toast('Enter a name');
    return;
  }

  if (rawInput.includes(',')) {
    const { importedCount, skippedLines } = parseData(rawInput);
    elements.nameInput.value = '';
    showSkippedWarning(elements.skippedCsv, skippedLines);
    toast(importedCount ? `Added ${importedCount} ${importedCount === 1 ? 'person' : 'people'}` : 'Could not parse - check format');
    maybeRefresh();
    return;
  }

  const start = elements.timeStart.value;
  const end = elements.timeEnd.value;
  if (start >= end) {
    toast('End must be after start');
    return;
  }

  const existingPerson = people.find(person => person.name.toLowerCase() === rawInput.toLowerCase());
  if (existingPerson) {
    existingPerson.ranges.push({ start, end });
  } else {
    people.push({ name: rawInput, ranges: [{ start, end }] });
  }

  elements.nameInput.value = '';
  people.sort((left, right) => left.name.localeCompare(right.name));
  renderNameList();
  maybeRefresh();
}

function renderNameList() {
  const amCount = countOnSheet(false);
  const pmCount = countOnSheet(true);

  elements.nameList.classList.toggle('has-names', people.length > 0);
  elements.peopleCount.textContent = people.length ? `${people.length} total · ${amCount} AM · ${pmCount} PM` : '';

  elements.badgeAM.textContent = amCount;
  elements.badgePM.textContent = pmCount;
  elements.badgeAM.classList.toggle('visible', amCount > 0);
  elements.badgePM.classList.toggle('visible', pmCount > 0);

  if (!people.length) {
    elements.nameList.innerHTML = '<p style="font-size: .7rem; color: var(--mut); text-align: center; padding: 8px 0">No names yet</p>';
    return;
  }

  elements.nameList.innerHTML = people.map((person, personIndex) => `
    <div class="name-entry">
      <div class="name-entry-top">
        <span>${escapeHtml(person.name)}</span>
        <button class="delete-btn" data-action="remove-person" data-person-index="${personIndex}">&times;</button>
      </div>
      ${person.ranges.map((range, rangeIndex) => `
        <div class="name-entry-range">
          <span>${formatTime12(range.start)}&ndash;${formatTime12(range.end)}</span>
          <button class="delete-btn" data-action="remove-range" data-person-index="${personIndex}" data-range-index="${rangeIndex}">&times;</button>
        </div>
      `).join('')}
    </div>
  `).join('');
}

function handleNameListClick(event) {
  const button = event.target.closest('button[data-action]');
  if (!button) {
    return;
  }

  const personIndex = Number(button.dataset.personIndex);
  if (!Number.isInteger(personIndex)) {
    return;
  }

  if (button.dataset.action === 'remove-person') {
    people.splice(personIndex, 1);
  } else if (button.dataset.action === 'remove-range') {
    const rangeIndex = Number(button.dataset.rangeIndex);
    if (!Number.isInteger(rangeIndex) || !people[personIndex]) {
      return;
    }
    people[personIndex].ranges.splice(rangeIndex, 1);
    if (!people[personIndex].ranges.length) {
      people.splice(personIndex, 1);
    }
  }

  renderNameList();
  maybeRefresh();
}

function resetRoomData() {
  ROOM_TIMES.forEach(timeValue => {
    roomData[timeValue] = { off: '', b: '', s: '' };
  });
}

function resetPreview(message) {
  releasePreviewUrl();
  elements.previewArea.className = 'preview-empty';
  elements.previewArea.style.display = '';
  elements.previewArea.innerHTML = `<div class="icon">&#128203;</div><p>${message}</p>`;
}

function clearNames() {
  if (!people.length && !Object.values(roomData).some(room => room.off || room.b || room.s)) {
    return;
  }
  if (!window.confirm('Clear all names and room data? This cannot be undone.')) {
    return;
  }

  people = [];
  resetRoomData();
  renderNameList();
  resetPreview('Add names then click Build Schedule.');
  toast('Cleared');
}

async function copyNamesAsCSV() {
  if (!people.length && !Object.values(roomData).some(room => room.off || room.b || room.s)) {
    toast('Nothing to copy');
    return;
  }

  const peopleLines = people.map(person => [person.name, ...person.ranges.flatMap(range => [range.start, range.end])].join(', '));
  const roomLines = ROOM_TIMES
    .filter(timeValue => roomData[timeValue].off || roomData[timeValue].b || roomData[timeValue].s)
    .map(timeValue => [timeValue, roomData[timeValue].off, roomData[timeValue].b, roomData[timeValue].s].join(', '));
  const csv = [...peopleLines, ...(roomLines.length ? ['', ...roomLines] : [])].join('\n');

  try {
    await navigator.clipboard.writeText(csv);
    toast('Copied to clipboard');
  } catch (error) {
    toast('Clipboard copy failed');
  }
}

function normalizeTime(timeValue) {
  let normalized = timeValue.trim().replace(/[aApP][mM]/g, '').trim();
  if (!normalized.includes(':')) {
    normalized += ':00';
  }
  const parts = normalized.split(':');
  const hours = parseInt(parts[0], 10);
  const minutes = parts[1] || '00';
  return `${hours < 10 ? `0${hours}` : hours}:${minutes}`;
}

function isValidTime(timeValue) {
  if (!timeValue || !/^\d{2}:\d{2}$/.test(timeValue)) {
    return false;
  }
  const minutes = toMinutes(timeValue);
  return minutes >= toMinutes('11:00') && minutes <= toMinutes('16:30');
}

function shouldReplaceExistingData() {
  return people.length > 0 || Object.values(roomData).some(room => room.off || room.b || room.s);
}

function handleCSV(input) {
  const file = input.files[0];
  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = event => {
    if (shouldReplaceExistingData()) {
      if (!window.confirm('This will replace all existing names and room data. Continue?')) {
        input.value = '';
        return;
      }
      people = [];
      resetRoomData();
    }

    const readerResult = event.target && typeof event.target.result === 'string' ? event.target.result : '';
    const { importedCount, skippedLines } = parseData(readerResult);
    showSkippedWarning(elements.skippedCsv, skippedLines);
    toast(`CSV imported - ${importedCount} added`);
    maybeRefresh();
    input.value = '';
  };
  reader.readAsText(file);
}

function importPaste() {
  const text = elements.pasteInput.value;
  if (!text.trim()) {
    return;
  }

  if (shouldReplaceExistingData()) {
    if (!window.confirm('This will replace all existing names and room data. Continue?')) {
      return;
    }
    people = [];
    resetRoomData();
  }

  const { importedCount, skippedLines } = parseData(text);
  elements.pasteInput.value = '';
  showSkippedWarning(elements.skippedPaste, skippedLines);
  toast(`Imported - ${importedCount} added`);
  maybeRefresh();
}

function showSkippedWarning(element, skippedLines) {
  if (!skippedLines.length) {
    element.classList.remove('visible');
    element.textContent = '';
    return;
  }

  element.innerHTML = `<strong>⚠ ${skippedLines.length} line(s) skipped:</strong>${skippedLines.map(line => (
    `<div style="font-family:monospace;margin-top:2px">${escapeHtml(line)}</div>`
  )).join('')}`;
  element.classList.add('visible');
}

function parseData(text) {
  let importedCount = 0;
  const skippedLines = [];

  text
    .split('\n')
    .map(line => line.trim())
    .filter(line => line && !line.toLowerCase().startsWith('name') && !line.startsWith('#'))
    .forEach(line => {
      const parts = line.split(',').map(part => part.trim());
      if (!parts.length) {
        return;
      }

      const normalizedFirst = normalizeTime(parts[0]);
      if (ROOM_TIMES.includes(normalizedFirst)) {
        roomData[normalizedFirst] = {
          off: normalizedFirst === '11:00' ? '' : (parts[1] || ''),
          b: parts[2] || '',
          s: parts[3] || '',
        };
        importedCount += 1;
        return;
      }

      if (parts.length < 3) {
        skippedLines.push(line);
        return;
      }

      const ranges = [];
      for (let index = 1; index + 1 < parts.length; index += 2) {
        if (!parts[index] || !parts[index + 1]) {
          continue;
        }
        const start = normalizeTime(parts[index]);
        const end = normalizeTime(parts[index + 1]);
        if (!isValidTime(start) || !isValidTime(end) || start >= end) {
          skippedLines.push(line);
          return;
        }
        ranges.push({ start, end });
      }

      if (!ranges.length) {
        skippedLines.push(line);
        return;
      }

      const existingPerson = people.find(person => person.name.toLowerCase() === parts[0].toLowerCase());
      if (existingPerson) {
        existingPerson.ranges.push(...ranges);
      } else {
        people.push({ name: parts[0], ranges });
      }
      importedCount += 1;
    });

  people.sort((left, right) => left.name.localeCompare(right.name));
  renderNameList();
  return { importedCount, skippedLines };
}

async function getErrorMessage(response, fallbackMessage) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const payload = await response.json();
    return payload.error || fallbackMessage;
  }
  const text = await response.text();
  return text || fallbackMessage;
}

function releasePreviewUrl() {
  if (currentPreviewUrl) {
    URL.revokeObjectURL(currentPreviewUrl);
    currentPreviewUrl = null;
  }
}

async function build() {
  if (!people.length) {
    resetPreview(`No people on ${isPM ? 'PM' : 'AM'} sheet.`);
    return;
  }

  elements.spinner.className = 'spinner show';
  elements.previewArea.style.display = 'none';

  try {
    const response = await fetch('/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ people, is_pm: isPM, room_data: roomData }),
    });
    if (!response.ok) {
      throw new Error(await getErrorMessage(response, 'Preview generation failed'));
    }

    const blob = await response.blob();
    releasePreviewUrl();
    currentPreviewUrl = URL.createObjectURL(blob);

    const image = document.createElement('img');
    image.src = currentPreviewUrl;
    image.alt = 'Schedule Preview';

    elements.spinner.className = 'spinner';
    elements.previewArea.style.display = '';
    elements.previewArea.className = 'preview-wrap';
    elements.previewArea.replaceChildren(image);

    const sheetPeople = people.filter(person => personOnSheet(person, isPM));
    if (sheetPeople.length > 18) {
      toast(`⚠ ${sheetPeople.length - 18} name(s) won't fit on ${isPM ? 'PM' : 'AM'} sheet - only 18 slots available`);
    } else {
      toast('Built!');
    }
  } catch (error) {
    elements.spinner.className = 'spinner';
    resetPreview('Build failed. Please review your input and try again.');
    toast(`Error: ${error.message}`);
  }
}

async function doExport() {
  if (!people.length) {
    toast('No people to export');
    return;
  }

  try {
    const response = await fetch('/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ people, room_data: roomData }),
    });
    if (!response.ok) {
      throw new Error(await getErrorMessage(response, 'Export generation failed'));
    }

    const blob = await response.blob();
    const filename = window.prompt('Save as:', todayFilename()) || todayFilename();

    if (window.showSaveFilePicker) {
      const handle = await window.showSaveFilePicker({
        suggestedName: filename,
        types: [{ description: 'Excel', accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] } }],
      });
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      toast('Exported!');
      return;
    }

    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(downloadUrl);
    toast('Exported!');
  } catch (error) {
    if (error.name !== 'AbortError') {
      toast(`Export failed: ${error.message}`);
    }
  }
}

function toast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add('show');
  window.setTimeout(() => elements.toast.classList.remove('show'), 2400);
}
