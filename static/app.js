  const { appVersion: APP_VERSION = 'dev', commitShort: APP_COMMIT_SHORT = 'unknown', commitSha: APP_COMMIT_SHA = 'unknown' } = document.body.dataset;
  const TIME_VALUES = ['11:00', '11:15', '11:30', '11:45', '12:00', '12:15', '12:30', '12:45', '13:00', '13:15', '13:30', '13:45', '14:00', '14:15', '14:30', '14:45', '15:00', '15:15', '15:30', '15:45', '16:00', '16:15', '16:30', '16:45'];
  const TIME_LABELS = ['11:00 AM', '11:15 AM', '11:30 AM', '11:45 AM', '12:00 PM', '12:15 PM', '12:30 PM', '12:45 PM', '1:00 PM', '1:15 PM', '1:30 PM', '1:45 PM', '2:00 PM', '2:15 PM', '2:30 PM', '2:45 PM', '3:00 PM', '3:15 PM', '3:30 PM', '3:45 PM', '4:00 PM', '4:15 PM', '4:30 PM', '4:45 PM'];
  const MANUAL_TIME_VALUES = TIME_VALUES.slice(0, -1);
  const MANUAL_TIME_LABELS = TIME_LABELS.slice(0, -1);
  const DRAFT_STORAGE_KEY = 'v-coordinator-draft-v1';
  const DRAFT_MAX_AGE_MS = 14 * 24 * 60 * 60 * 1000;

  const AM_TIMES = ['11:00', '11:30', '12:00', '12:30', '13:00'];
  const PM_TIMES = ['14:00', '14:30', '15:00', '15:30', '16:00'];

  let people = [], isPM = false, sidebarOpen = true, isLightMode = false, autoRefresh = false;
  let currentInputTab = 'paste';
  let currentAccent = localStorage.getItem('accent') || 'lime';
  let currentPreviewUrl = null;
  let toastTimeoutId = null;
  let commitChipResetTimeoutId = null;
  let lastBuiltText = 'Not built yet';
  let lastFocusedElement = null;
  let confirmResolver = null;
  let confirmFallbackFocusId = 'helpBtn';

  const ROOM_TIMES = ['11:00', '11:30', '12:00', '12:30', '13:00', '14:00', '14:30', '15:00', '15:30', '16:00'];
  const ACCENT_OPTIONS = ['lime', 'blue', 'purple', 'green', 'red', 'cyan', 'orange', 'pink', 'teal'];
  let roomData = {};
  ROOM_TIMES.forEach(t => roomData[t] = { off: '', b: '', s: '' });

  ['timeStart', 'timeEnd'].forEach(id => {
    const select = document.getElementById(id);
    select.innerHTML = MANUAL_TIME_VALUES.map((t, i) => `<option value="${t}">${MANUAL_TIME_LABELS[i]}</option>`).join('');
  });
  document.getElementById('timeEnd').value = '11:30';

  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
      e.preventDefault();
      build();
    }
  });

  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    isLightMode = true;
    document.body.classList.add('light');
    document.getElementById('themeBtn').textContent = '🌙';
    document.getElementById('themeBtn').title = 'Switch to dark mode';
  }
  setAccent(currentAccent, false);

  function toggleTheme() {
    isLightMode = !isLightMode;
    document.body.classList.toggle('light', isLightMode);
    document.getElementById('themeBtn').textContent = isLightMode ? '🌙' : '☀️';
    document.getElementById('themeBtn').title = isLightMode ? 'Switch to dark mode' : 'Switch to light mode';
    localStorage.setItem('theme', isLightMode ? 'light' : 'dark');
  }

  function setAccent(accent, save = true) {
    if (!ACCENT_OPTIONS.includes(accent)) accent = 'lime';
    document.body.classList.remove(
      'accent-lime', 'accent-blue', 'accent-purple', 'accent-green', 'accent-red',
      'accent-cyan', 'accent-orange', 'accent-pink', 'accent-teal'
    );
    document.body.classList.add('accent-' + accent);
    currentAccent = accent;
    document.getElementById('accentSelect').value = accent;
    if (save) {
      localStorage.setItem('accent', accent);
      saveDraft();
    }
  }

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
    const btn = document.getElementById('toggleBtn');
    document.getElementById('app').classList.toggle('collapsed', !sidebarOpen);
    btn.innerHTML = sidebarOpen ? '&#8249;' : '&#8250;';
    btn.title = sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar';
    btn.classList.toggle('collapsed', !sidebarOpen);
  }

  function formatDraftTimestamp(timestamp) {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return 'recently';
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  }

  function normalizeDraftRoomData(rawRoomData) {
    const normalized = {};
    ROOM_TIMES.forEach(time => {
      const source = rawRoomData && typeof rawRoomData === 'object' ? rawRoomData[time] : null;
      normalized[time] = {
        off: time === '11:00' ? '' : String(source && source.off ? source.off : ''),
        b: String(source && source.b ? source.b : ''),
        s: String(source && source.s ? source.s : '')
      };
    });
    return normalized;
  }

  function normalizeDraftPeople(rawPeople) {
    if (!Array.isArray(rawPeople)) return [];

    return rawPeople
      .map(person => {
        const name = person && typeof person.name === 'string' ? person.name.trim() : '';
        const rawRanges = Array.isArray(person && person.ranges) ? person.ranges : [];
        const ranges = rawRanges.filter(range =>
          range &&
          isValidTime(range.start) &&
          isValidTime(range.end) &&
          toMinutes(range.start) < toMinutes(range.end)
        ).map(range => ({ start: range.start, end: range.end }));

        return { name, ranges };
      })
      .filter(person => person.name && person.ranges.length)
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  function hasStoredDraft() {
    try {
      const raw = localStorage.getItem(DRAFT_STORAGE_KEY);
      if (!raw) return false;

      const draft = JSON.parse(raw);
      const savedAt = Number(draft && draft.saved_at);
      if (!savedAt || (Date.now() - savedAt) > DRAFT_MAX_AGE_MS) {
        localStorage.removeItem(DRAFT_STORAGE_KEY);
        return false;
      }

      return true;
    } catch (e) {
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      return false;
    }
  }

  function updateDraftButton() {
    const clearDraftBtn = document.getElementById('clearDraftBtn');
    if (!clearDraftBtn) return;

    const hasDraft = hasStoredDraft();
    clearDraftBtn.disabled = !hasDraft;
    clearDraftBtn.title = hasDraft ? 'Clear the saved browser draft' : 'No saved draft to clear';
  }

  function saveDraft() {
    try {
      if (!hasImportedData()) {
        localStorage.removeItem(DRAFT_STORAGE_KEY);
        updateDraftButton();
        return;
      }

      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({
        saved_at: Date.now(),
        people,
        room_data: roomData,
        is_pm: isPM,
        accent: currentAccent,
        input_tab: currentInputTab
      }));
      updateDraftButton();
    } catch (e) {
      // Ignore storage failures and keep the app usable.
    }
  }

  function restoreDraft() {
    let draft = null;

    try {
      const raw = localStorage.getItem(DRAFT_STORAGE_KEY);
      if (!raw) {
        updateDraftButton();
        return;
      }
      draft = JSON.parse(raw);
    } catch (e) {
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      updateDraftButton();
      return;
    }

    const savedAt = Number(draft && draft.saved_at);
    if (!savedAt || (Date.now() - savedAt) > DRAFT_MAX_AGE_MS) {
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      updateDraftButton();
      return;
    }

    people = normalizeDraftPeople(draft.people);
    roomData = normalizeDraftRoomData(draft.room_data);
    isPM = !!draft.is_pm;
    currentInputTab = ['manual', 'csv', 'paste'].includes(draft.input_tab) ? draft.input_tab : 'paste';

    if (draft.accent) {
      setAccent(draft.accent);
    }

    renderNameList();
    switchTab(currentInputTab);
    renderHeaderStatus();
    renderGenerateMeta();
    setInlineStatus(`Draft restored from ${formatDraftTimestamp(savedAt)}.`, 'info');
    toast('Draft restored');
    updateDraftButton();
  }

  function getActiveModalOverlay() {
    const confirmModal = document.getElementById('confirmModal');
    if (confirmModal.classList.contains('show')) return confirmModal;

    const helpModal = document.getElementById('helpModal');
    if (helpModal.classList.contains('show')) return helpModal;

    return null;
  }

  function getFocusableModalElements(overlay = getActiveModalOverlay()) {
    const modal = overlay ? overlay.querySelector('.modal') : null;
    if (!modal) return [];
    return Array.from(modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'))
      .filter(el => !el.disabled && el.offsetParent !== null);
  }

  function openModal(overlayId, fallbackFocusId = 'helpBtn') {
    const overlay = document.getElementById(overlayId);
    const modalCard = overlay.querySelector('.modal');

    if (!getActiveModalOverlay()) {
      lastFocusedElement = document.activeElement;
    }

    confirmFallbackFocusId = fallbackFocusId;
    overlay.classList.add('show');

    setTimeout(() => {
      const focusable = getFocusableModalElements(overlay);
      (focusable[0] || modalCard).focus();
    }, 0);
  }

  function closeModal(overlayId, fallbackFocusId = confirmFallbackFocusId) {
    const overlay = document.getElementById(overlayId);
    overlay.classList.remove('show');

    if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
      lastFocusedElement.focus();
    } else {
      const fallback = document.getElementById(fallbackFocusId);
      if (fallback) fallback.focus();
    }
  }

  function handleModalKeydown(e) {
    const activeModal = getActiveModalOverlay();
    if (!activeModal) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      if (activeModal.id === 'confirmModal') {
        resolveConfirm(false);
      } else {
        toggleHelp(false);
      }
      return;
    }

    if (e.key !== 'Tab') return;

    const focusable = getFocusableModalElements(activeModal);
    if (!focusable.length) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  function toggleHelp(forceOpen) {
    const helpModal = document.getElementById('helpModal');
    const shouldOpen = typeof forceOpen === 'boolean' ? forceOpen : !helpModal.classList.contains('show');

    if (shouldOpen) {
      openModal('helpModal', 'helpBtn');
      return;
    }

    closeModal('helpModal', 'helpBtn');
  }

  function askForConfirmation(message, acceptLabel = 'Continue') {
    const confirmModal = document.getElementById('confirmModal');
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmAcceptBtn').textContent = acceptLabel;

    return new Promise(resolve => {
      confirmResolver = resolve;
      openModal('confirmModal');
    });
  }

  function resolveConfirm(accepted) {
    const resolver = confirmResolver;
    confirmResolver = null;
    closeModal('confirmModal');
    if (resolver) resolver(accepted);
  }

  document.addEventListener('keydown', handleModalKeydown);

  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    document.getElementById('autoRefreshBtn').classList.toggle('active', autoRefresh);
    document.getElementById('autoRefreshBtn').title = autoRefresh ? 'Auto-refresh on' : 'Auto-refresh off';
    toast(autoRefresh ? 'Auto-refresh on' : 'Auto-refresh off');
  }

  function maybeRefresh() {
    if (autoRefresh && document.getElementById('previewArea').className !== 'preview-empty') build();
  }

  function selectSheet(pm) {
    isPM = pm;
    ['AM', 'PM'].forEach(x =>
      document.getElementById('tab-sheet-' + x).classList.toggle('active', pm ? (x === 'PM') : (x === 'AM'))
    );
    renderHeaderStatus();
    saveDraft();
    if (document.getElementById('previewArea').className !== 'preview-empty') build();
  }

  function toMinutes(timeStr) {
    if (!timeStr) return 0;
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
  }

  function countOnSheet(sheetIsPM) {
    const domainTimes = sheetIsPM ? PM_TIMES : AM_TIMES;
    const domainStart = toMinutes(domainTimes[0]);
    const domainEnd   = toMinutes(domainTimes[domainTimes.length - 1]) + 30;
    return people.filter(person =>
      person.ranges.some(r => toMinutes(r.start) < domainEnd && toMinutes(r.end) > domainStart)
    ).length;
  }

  function formatTime12(t) {
    if (!t) return '';
    const [h, m] = t.split(':').map(Number);
    const period = h >= 12 ? 'PM' : 'AM';
    const hour12 = h > 12 ? h - 12 : (h === 0 ? 12 : h);
    return hour12 + ':' + (m < 10 ? '0' + m : m) + ' ' + period;
  }

  function escapeHTML(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function todayFilename() {
    const now = new Date();
    const y   = now.getFullYear();
    const mo  = String(now.getMonth() + 1).padStart(2, '0');
    const d   = String(now.getDate()).padStart(2, '0');
    return `schedule-${y}-${mo}-${d}.xlsx`;
  }

  function releasePreviewUrl() {
    if (currentPreviewUrl) {
      URL.revokeObjectURL(currentPreviewUrl);
      currentPreviewUrl = null;
    }
  }

  function resetRoomData() {
    ROOM_TIMES.forEach(t => roomData[t] = { off: '', b: '', s: '' });
  }

  function hasImportedData() {
    return people.length > 0 || Object.values(roomData).some(r => r.off || r.b || r.s);
  }

  function resetPreview(message) {
    releasePreviewUrl();
    const previewArea = document.getElementById('previewArea');
    previewArea.classList.remove('preview-hidden');
    previewArea.className = 'preview-empty';
    previewArea.innerHTML = `<div class="icon">&#128203;</div><p>${message}</p>`;
  }

  function setInlineStatus(message, type = 'info') {
    const statusEl = document.getElementById('inlineStatus');
    statusEl.textContent = message;
    statusEl.className = `inline-status visible ${type}`;
  }

  function updateLastBuiltLabel() {
    const now = new Date();
    lastBuiltText = `Last built ${now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
    renderGenerateMeta();
  }

  function renderGenerateMeta() {
    const metaEl = document.getElementById('generateMeta');
    if (!metaEl) return;

    const amCount = countOnSheet(false);
    const pmCount = countOnSheet(true);

    if (!people.length) {
      metaEl.textContent = `No names loaded yet · ${lastBuiltText}`;
      return;
    }

    metaEl.textContent = `${people.length} total · ${amCount} AM · ${pmCount} PM · ${lastBuiltText}`;
  }

  function renderHeaderStatus() {
    document.getElementById('headerStatus').innerHTML = (isPM ? 'PM Sheet' : 'AM Sheet') + `&nbsp;&middot;&nbsp; v${APP_VERSION} &nbsp;&middot;&nbsp; <span class="build-meta"><button class="commit-chip" id="commitChip" type="button" title="Copy full build commit">${APP_COMMIT_SHORT}</button></span>`;
    document.getElementById('previewTitle').textContent = (isPM ? 'P.M.' : 'A.M.') + ' - ' + (isPM ? 'PM' : 'AM');
  }

  function showCommitChipCopiedState() {
    const commitChip = document.getElementById('commitChip');
    if (!commitChip) return;

    if (commitChipResetTimeoutId) clearTimeout(commitChipResetTimeoutId);
    commitChip.textContent = 'Copied';
    commitChip.classList.add('copied');
    commitChipResetTimeoutId = setTimeout(() => {
      commitChip.textContent = APP_COMMIT_SHORT;
      commitChip.classList.remove('copied');
      commitChipResetTimeoutId = null;
    }, 1500);
  }

  async function copyCommitSha() {
    const commitSha = APP_COMMIT_SHA;
    if (!commitSha || commitSha === 'unknown') {
      toast('Commit SHA unavailable');
      return;
    }

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(commitSha);
      } else {
        const tempInput = document.createElement('textarea');
        tempInput.value = commitSha;
        tempInput.setAttribute('readonly', '');
        tempInput.className = 'clipboard-fallback';
        document.body.appendChild(tempInput);
        tempInput.select();
        tempInput.setSelectionRange(0, tempInput.value.length);
        const copied = document.execCommand('copy');
        document.body.removeChild(tempInput);
        if (!copied) {
          throw new Error('execCommand copy failed');
        }
      }
      showCommitChipCopiedState();
      toast('Copied build commit');
    } catch (e) {
      window.prompt('Copy build commit:', commitSha);
    }
  }

  function switchTab(tab) {
    currentInputTab = tab;
    ['manual', 'csv', 'paste'].forEach(x => {
      document.getElementById('tab-' + x).classList.toggle('active', x === tab);
      document.getElementById('panel-' + x).classList.toggle('is-hidden', x !== tab);
    });

    showSkippedWarning('skipped-csv', []);
    showSkippedWarning('skipped-paste', []);

    if (tab === 'manual') {
      document.getElementById('nameInput').focus();
    } else if (tab === 'paste') {
      document.getElementById('pasteInput').focus();
    }

    saveDraft();
  }

  function addName() {
    const rawInput = document.getElementById('nameInput').value.trim();
    if (!rawInput) { toast('Enter a name'); return; }

    if (rawInput.includes(',')) {
      const { imported, skipped } = parseData(rawInput);
      document.getElementById('nameInput').value = '';
      showSkippedWarning('skipped-csv', skipped);
      if (imported) toast(`Added ${imported} ${imported === 1 ? 'person' : 'people'}`);
      else toast('Could not parse - check format');
      maybeRefresh();
      return;
    }

    const name  = rawInput;
    const start = document.getElementById('timeStart').value;
    const end   = document.getElementById('timeEnd').value;
    if (start >= end) { toast('End must be after start'); return; }
    const existing = people.find(p => p.name.toLowerCase() === name.toLowerCase());
    if (existing) {
      existing.ranges.push({ start, end });
    } else {
      people.push({ name, ranges: [{ start, end }] });
    }
    document.getElementById('nameInput').value = '';
    people.sort((a, b) => a.name.localeCompare(b.name));
    renderNameList();
    maybeRefresh();
  }

  function renderNameList() {
    const container = document.getElementById('nameList');
    const countEl   = document.getElementById('peopleCount');
    const amCount   = countOnSheet(false);
    const pmCount   = countOnSheet(true);

    container.classList.toggle('has-names', people.length > 0);
    renderGenerateMeta();
    saveDraft();

    if (people.length) {
      countEl.textContent = `${people.length} total · ${amCount} AM · ${pmCount} PM`;
    } else {
      countEl.textContent = '';
    }

    const amBadge = document.getElementById('badge-AM');
    const pmBadge = document.getElementById('badge-PM');
    amBadge.textContent = amCount;
    pmBadge.textContent = pmCount;
    amBadge.classList.toggle('visible', amCount > 0);
    pmBadge.classList.toggle('visible', pmCount > 0);

    if (!people.length) {
      container.innerHTML = '<p class="empty-name-list">No names yet</p>';
      return;
    }

    container.innerHTML = people.map((person, pi) => `
      <div class="name-entry">
        <div class="name-entry-top">
          <span>${escapeHTML(person.name)}</span>
          <button class="delete-btn" data-action="remove-person" data-person-index="${pi}">&times;</button>
        </div>
        ${person.ranges.map((range, ri) => `
          <div class="name-entry-range">
            <span>${formatTime12(range.start)}&ndash;${formatTime12(range.end)}</span>
            <button class="delete-btn" data-action="remove-range" data-person-index="${pi}" data-range-index="${ri}">&times;</button>
          </div>
        `).join('')}
      </div>
    `).join('');
  }

  function removeRange(personIndex, rangeIndex) {
    people[personIndex].ranges.splice(rangeIndex, 1);
    if (!people[personIndex].ranges.length) people.splice(personIndex, 1);
    renderNameList();
    maybeRefresh();
  }

  function removePerson(personIndex) {
    people.splice(personIndex, 1);
    renderNameList();
    maybeRefresh();
  }

  async function clearNames() {
    if (!hasImportedData()) return;
    const confirmed = await askForConfirmation('Clear all names and room data? This cannot be undone.', 'Clear all');
    if (!confirmed) return;
    people = [];
    resetRoomData();
    localStorage.removeItem(DRAFT_STORAGE_KEY);
    updateDraftButton();
    renderNameList();
    resetPreview('Add names, paste data, or import CSV, then click Build Schedule.');
    setInlineStatus('Cleared all names and room data. Saved draft removed.', 'info');
    toast('Cleared');
  }

  async function clearDraft() {
    if (!hasStoredDraft()) {
      updateDraftButton();
      setInlineStatus('No saved draft to clear.', 'info');
      toast('No saved draft');
      return;
    }

    const confirmed = await askForConfirmation('Clear the saved browser draft? Your current page will stay as-is until you make another change.', 'Clear draft');
    if (!confirmed) return;

    localStorage.removeItem(DRAFT_STORAGE_KEY);
    updateDraftButton();
    setInlineStatus('Saved draft cleared for this browser.', 'info');
    toast('Draft cleared');
  }

  function copyNamesAsCSV() {
    if (!hasImportedData()) {
      setInlineStatus('Nothing to copy yet.', 'info');
      toast('Nothing to copy');
      return;
    }
    const peopleLines = people.map(person =>
      [person.name, ...person.ranges.flatMap(r => [r.start, r.end])].join(', ')
    );
    const roomLines = ROOM_TIMES
      .filter(t => roomData[t].off || roomData[t].b || roomData[t].s)
      .map(t => [t, roomData[t].off, roomData[t].b, roomData[t].s].join(', '));
    const csv = [...peopleLines, ...(roomLines.length ? ['', ...roomLines] : [])].join('\n');
    navigator.clipboard.writeText(csv)
      .then(() => {
        setInlineStatus('Copied current names and room data to the clipboard.', 'success');
        toast('Copied to clipboard');
      })
      .catch(() => {
        setInlineStatus('Could not copy data to the clipboard in this browser.', 'error');
        toast('Clipboard copy failed');
      });
  }

  function normalizeTime(t) {
    const raw = String(t || '').trim();
    if (!raw) return '';

    const meridiemMatch = raw.match(/\b([aApP])[mM]\b/);
    const meridiem = meridiemMatch ? meridiemMatch[1].toUpperCase() : '';
    let normalized = raw.replace(/[aApP][mM]/g, '').replace(/\s+/g, '');
    if (!normalized.includes(':')) normalized += ':00';

    const parts = normalized.split(':');
    let h = parseInt(parts[0], 10);
    let m = parseInt(parts[1] || '0', 10);
    if (!Number.isInteger(h) || !Number.isInteger(m) || m < 0 || m > 59) return '';

    if (meridiem === 'P' && h < 12) {
      h += 12;
    } else if (meridiem === 'A' && h === 12) {
      h = 0;
    } else if (!meridiem && h >= 1 && h <= 4) {
      h += 12;
    }

    return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
  }

  function isValidTime(t) {
    if (!t || !t.match(/^\d{2}:\d{2}$/)) return false;
    return TIME_VALUES.includes(t);
  }

  function validatePeopleBeforeSubmit() {
    for (let personIndex = 0; personIndex < people.length; personIndex++) {
      const person = people[personIndex];
      if (!person || !Array.isArray(person.ranges)) {
        return `Person ${personIndex + 1} is missing schedule ranges`;
      }

      for (let rangeIndex = 0; rangeIndex < person.ranges.length; rangeIndex++) {
        const range = person.ranges[rangeIndex];
        if (!range || !isValidTime(range.start) || !isValidTime(range.end)) {
          return `${person.name}: range ${rangeIndex + 1} must use 15-minute times between 11:00 and 16:45`;
        }
        if (toMinutes(range.start) >= toMinutes(range.end)) {
          return `${person.name}: range ${rangeIndex + 1} must end after it starts`;
        }
      }
    }

    return '';
  }

  function handleCSV(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async e => {
      if (hasImportedData()) {
        const confirmed = await askForConfirmation('This will replace all existing names and room data. Continue?', 'Replace data');
        if (!confirmed) {
          input.value = '';
          return;
        }
        people = [];
        resetRoomData();
      }
      const text = e.target && typeof e.target.result === 'string' ? e.target.result : '';
      const { imported, skipped } = parseData(text);
      showSkippedWarning('skipped-csv', skipped);
      setInlineStatus(
        skipped.length
          ? `Imported ${imported} line(s). ${skipped.length} line(s) were skipped.`
          : `Imported ${imported} line(s) from CSV.`,
        skipped.length ? 'info' : 'success'
      );
      toast(`CSV imported - ${imported} added`);
      maybeRefresh();
      input.value = '';
    };
    reader.readAsText(file);
  }

  async function importPaste() {
    const text = document.getElementById('pasteInput').value;
    if (!text.trim()) return;

    if (hasImportedData()) {
      const confirmed = await askForConfirmation('This will replace all existing names and room data. Continue?', 'Replace data');
      if (!confirmed) return;
      people = [];
      resetRoomData();
    }

    const { imported, skipped } = parseData(text);
    document.getElementById('pasteInput').value = '';
    showSkippedWarning('skipped-paste', skipped);
    setInlineStatus(
      skipped.length
        ? `Imported ${imported} line(s). ${skipped.length} pasted line(s) were skipped.`
        : `Imported ${imported} line(s) from pasted data.`,
      skipped.length ? 'info' : 'success'
    );
    toast(`Imported - ${imported} added`);
    maybeRefresh();
  }

  function showSkippedWarning(elementId, skippedLines) {
    const warningEl = document.getElementById(elementId);
    if (!skippedLines.length) {
      warningEl.classList.remove('visible');
      warningEl.textContent = '';
      return;
    }
    warningEl.innerHTML = `<strong>⚠ ${skippedLines.length} line(s) skipped:</strong>` +
      skippedLines.map(l => `<div class="skipped-line">${escapeHTML(l)}</div>`).join('');
    warningEl.classList.add('visible');
  }

  function parseData(text) {
    let imported = 0;
    const skipped = [];

    text.split('\n').map(l => l.trim()).filter(l => l && !l.toLowerCase().startsWith('name') && !l.startsWith('#')).forEach(line => {
      const parts = line.split(',').map(x => x.trim());
      if (!parts.length) return;

      const normalizedFirst = normalizeTime(parts[0]);
      if (ROOM_TIMES.includes(normalizedFirst)) {
        roomData[normalizedFirst] = {
          off: normalizedFirst === '11:00' ? '' : (parts[1] || ''),
          b:   parts[2] || '',
          s:   parts[3] || '',
        };
        imported++;
        return;
      }

      if (parts.length < 3) { skipped.push(line); return; }

      const ranges = [];
      for (let i = 1; i + 1 < parts.length; i += 2) {
        if (!parts[i] || !parts[i + 1]) continue;
        const start = normalizeTime(parts[i]);
        const end   = normalizeTime(parts[i + 1]);
        if (!isValidTime(start) || !isValidTime(end) || start >= end) {
          skipped.push(line);
          return;
        }
        ranges.push({ start, end });
      }

      if (!ranges.length) { skipped.push(line); return; }

      const existing = people.find(x => x.name.toLowerCase() === parts[0].toLowerCase());
      if (existing) {
        existing.ranges.push(...ranges);
      } else {
        people.push({ name: parts[0], ranges });
      }
      imported++;
    });

    people.sort((a, b) => a.name.localeCompare(b.name));
    renderNameList();
    return { imported, skipped };
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

  async function build() {
    const spinner     = document.getElementById('spinner');
    const previewArea = document.getElementById('previewArea');

    if (!people.length) {
      const sheetName = isPM ? 'PM' : 'AM';
      resetPreview(`No one currently overlaps the ${sheetName} sheet. Adjust times, import more data, or switch sheets.`);
      setInlineStatus(`No people available to build on the ${sheetName} sheet yet.`, 'info');
      return;
    }

    const validationError = validatePeopleBeforeSubmit();
    if (validationError) {
      resetPreview('Build failed. Please review your input and try again.');
      setInlineStatus(validationError, 'error');
      toast('Error: ' + validationError);
      return;
    }

    spinner.className = 'spinner show';
    previewArea.classList.add('preview-hidden');

    try {
      const res = await fetch('/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ people, is_pm: isPM, room_data: roomData })
      });
      if (!res.ok) throw new Error(await getErrorMessage(res, 'Preview generation failed'));
      const blob = await res.blob();
      releasePreviewUrl();
      currentPreviewUrl = URL.createObjectURL(blob);
      spinner.className = 'spinner';
      previewArea.classList.remove('preview-hidden');
      previewArea.className = 'preview-wrap';
      previewArea.innerHTML = `<img src="${currentPreviewUrl}" alt="Schedule Preview">`;
      const sheetPeople = people.filter(p => {
        const domainTimes = isPM ? PM_TIMES : AM_TIMES;
        const domainStart = toMinutes(domainTimes[0]);
        const domainEnd   = toMinutes(domainTimes[domainTimes.length - 1]) + 30;
        return p.ranges.some(r => toMinutes(r.start) < domainEnd && toMinutes(r.end) > domainStart);
      });
      if (sheetPeople.length > 18) {
        updateLastBuiltLabel();
        setInlineStatus(`${sheetPeople.length} people overlap the ${isPM ? 'PM' : 'AM'} sheet. Only 18 slots fit on the preview.`, 'info');
        toast(`⚠ ${sheetPeople.length - 18} name(s) won't fit on ${isPM ? 'PM' : 'AM'} sheet - only 18 slots available`);
      } else {
        updateLastBuiltLabel();
        setInlineStatus(`Built ${isPM ? 'PM' : 'AM'} preview for ${sheetPeople.length} visible people.`, 'success');
        toast('Built!');
      }
    } catch (e) {
      spinner.className = 'spinner';
      previewArea.classList.remove('preview-hidden');
      if (previewArea.className !== 'preview-wrap') {
        resetPreview('Build failed. Please review your input and try again.');
      }
      setInlineStatus(e.message || 'Preview generation failed.', 'error');
      toast('Error: ' + e.message);
    }
  }

  async function doExport() {
    if (!people.length) {
      setInlineStatus('No people available to export yet.', 'info');
      toast('No people to export');
      return;
    }

    const validationError = validatePeopleBeforeSubmit();
    if (validationError) {
      setInlineStatus(validationError, 'error');
      toast('Export failed: ' + validationError);
      return;
    }

    try {
      const res = await fetch('/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ people, room_data: roomData })
      });
      if (!res.ok) throw new Error(await getErrorMessage(res, 'Export generation failed'));
      const blob     = await res.blob();
      const filename = prompt('Save as:', todayFilename()) || todayFilename();

      if (window.showSaveFilePicker) {
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{ description: 'Excel', accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] } }]
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        setInlineStatus('Export completed successfully.', 'success');
        toast('Exported!');
      } else {
        const url = URL.createObjectURL(blob);
        const a   = document.createElement('a');
        a.href     = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        setInlineStatus('Export completed successfully.', 'success');
        toast('Exported!');
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        setInlineStatus(e.message || 'Export generation failed.', 'error');
        toast('Export failed: ' + e.message);
      }
    }
  }

  function toast(msg) {
    const toastEl = document.getElementById('toast');
    if (toastTimeoutId) clearTimeout(toastTimeoutId);
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    toastTimeoutId = setTimeout(() => {
      toastEl.classList.remove('show');
      toastTimeoutId = null;
    }, 2400);
  }

  document.getElementById('accentSelect').addEventListener('change', event => setAccent(event.target.value));
  document.getElementById('helpBtn').addEventListener('click', () => toggleHelp());
  document.getElementById('themeBtn').addEventListener('click', toggleTheme);
  document.getElementById('headerStatus').addEventListener('click', event => {
    if (event.target.closest('#commitChip')) copyCommitSha();
  });
  document.querySelectorAll('[data-sheet]').forEach(tab => {
    tab.addEventListener('click', () => selectSheet(tab.dataset.sheet === 'PM'));
  });
  document.querySelectorAll('[data-input-tab]').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.inputTab));
  });
  document.getElementById('nameInput').addEventListener('keydown', event => {
    if (event.key === 'Enter') addName();
  });
  document.getElementById('addNameBtn').addEventListener('click', addName);
  document.getElementById('clearNamesBtn').addEventListener('click', clearNames);
  document.getElementById('copyCsvBtn').addEventListener('click', copyNamesAsCSV);
  document.getElementById('clearDraftBtn').addEventListener('click', clearDraft);
  document.getElementById('csvInput').addEventListener('change', event => handleCSV(event.target));
  document.getElementById('importPasteBtn').addEventListener('click', importPaste);
  document.getElementById('buildBtn').addEventListener('click', build);
  document.getElementById('autoRefreshBtn').addEventListener('click', toggleAutoRefresh);
  document.getElementById('exportBtn').addEventListener('click', doExport);
  document.getElementById('toggleBtn').addEventListener('click', toggleSidebar);
  document.getElementById('helpModal').addEventListener('click', event => {
    if (event.target === event.currentTarget) toggleHelp();
  });
  document.getElementById('helpCloseBtn').addEventListener('click', () => toggleHelp());
  document.getElementById('confirmModal').addEventListener('click', event => {
    if (event.target === event.currentTarget) resolveConfirm(false);
  });
  document.getElementById('confirmCancelBtn').addEventListener('click', () => resolveConfirm(false));
  document.getElementById('confirmAcceptBtn').addEventListener('click', () => resolveConfirm(true));
  document.getElementById('nameList').addEventListener('click', event => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    const personIndex = Number(button.dataset.personIndex);
    if (!Number.isInteger(personIndex)) return;
    if (button.dataset.action === 'remove-person') {
      removePerson(personIndex);
      return;
    }
    const rangeIndex = Number(button.dataset.rangeIndex);
    if (button.dataset.action === 'remove-range' && Number.isInteger(rangeIndex)) {
      removeRange(personIndex, rangeIndex);
    }
  });

  renderHeaderStatus();
  renderGenerateMeta();
  updateDraftButton();
  restoreDraft();
