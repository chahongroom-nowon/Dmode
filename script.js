// 전역 변수
let currentDate = new Date();
let employees = [];
let teams = [];
let vacations = [];
let breakRecords = [];
let lastSyncTime = null;
let syncInterval = null;

// DOM 요소들
const elements = {
    currentDateDisplay: document.getElementById('current-date'),
    datePickerBtn: document.getElementById('date-picker-btn'),
    teamsContainer: document.getElementById('teams-container'),
    hamburgerBtn: document.getElementById('hamburger-btn'),
    hamburgerMenu: document.getElementById('hamburger-menu'),
    closeMenuBtn: document.getElementById('close-menu-btn'),
    menuOverlay: document.getElementById('menu-overlay'),
    
    // 모달들
    dateModal: document.getElementById('date-modal'),
    addEmployeeModal: document.getElementById('add-employee-modal'),
    editEmployeeModal: document.getElementById('edit-employee-modal'),
    deleteEmployeeModal: document.getElementById('delete-employee-modal'),
    editTeamModal: document.getElementById('edit-team-modal'),
    addVacationModal: document.getElementById('add-vacation-modal'),
    cancelVacationModal: document.getElementById('cancel-vacation-modal'),
    adminModal: document.getElementById('admin-modal'),
    passwordModal: document.getElementById('password-modal'),
    
    // 폼 요소들
    dateInput: document.getElementById('date-input'),
    employeeName: document.getElementById('employee-name'),
    employeeTeam: document.getElementById('employee-team'),
    employeeOffDays: document.getElementById('employee-off-days'),
    editEmployeeSelect: document.getElementById('edit-employee-select'),
    editEmployeeName: document.getElementById('edit-employee-name'),
    editEmployeeTeam: document.getElementById('edit-employee-team'),
    editEmployeeOffDays: document.getElementById('edit-employee-off-days'),
    deleteEmployeeSelect: document.getElementById('delete-employee-select'),
    editTeamSelect: document.getElementById('edit-team-select'),
    editTeamName: document.getElementById('edit-team-name'),
    editTeamOffDays: document.getElementById('edit-team-off-days'),
    vacationEmployeeSelect: document.getElementById('vacation-employee-select'),
    vacationDate: document.getElementById('vacation-date'),
    cancelVacationSelect: document.getElementById('cancel-vacation-select'),
    adminEmployeeSelect: document.getElementById('admin-employee-select'),
    adminDate: document.getElementById('admin-date'),
    adminBreakDown: document.getElementById('admin-break-down'),
    adminBreakUp: document.getElementById('admin-break-up'),
    passwordInput: document.getElementById('password-input')
};

// 데이터베이스 초기화
async function initDatabase() {
    // 서버에서 데이터 로드
    await loadDataFromServer();
    
    // 실시간 동기화 시작
    startRealtimeSync();
}

// 서버에서 데이터 로드
async function loadDataFromServer() {
    try {
        const response = await fetch('/api/data');
        if (response.ok) {
            const data = await response.json();
            employees = data.employees || [];
            teams = data.teams || [];
            vacations = data.vacations || [];
            breakRecords = data.breakRecords || [];
            lastSyncTime = data.lastUpdated;
            console.log('서버에서 데이터를 로드했습니다:', employees.length + '명의 직원');
            
            // 데이터 로드 후 즉시 UI 업데이트
            loadEmployees();
        } else {
            console.log('서버에서 데이터를 로드할 수 없습니다. 로컬 데이터를 사용합니다.');
            loadLocalData();
            loadEmployees();
        }
    } catch (error) {
        console.log('서버 연결 실패. 로컬 데이터를 사용합니다.');
        loadLocalData();
        loadEmployees();
    }
}

// 로컬 데이터 로드 (서버 연결 실패 시)
function loadLocalData() {
    const data = localStorage.getItem('dModeData');
    if (data) {
        const parsed = JSON.parse(data);
        employees = parsed.employees || [];
        teams = parsed.teams || [];
        vacations = parsed.vacations || [];
        breakRecords = parsed.breakRecords || [];
    } else {
        employees = [];
        teams = [];
        vacations = [];
        breakRecords = [];
    }
}

// 실시간 동기화 시작
function startRealtimeSync() {
    // 2초마다 서버와 동기화
    syncInterval = setInterval(syncWithServer, 2000);
    console.log('실시간 동기화가 시작되었습니다.');
}

// 서버와 동기화
async function syncWithServer() {
    try {
        const response = await fetch('/api/data');
        if (response.ok) {
            const data = await response.json();
            if (data.lastUpdated !== lastSyncTime) {
                employees = data.employees || [];
                teams = data.teams || [];
                vacations = data.vacations || [];
                breakRecords = data.breakRecords || [];
                lastSyncTime = data.lastUpdated;
                
                // UI 업데이트
                loadEmployees();
                console.log('데이터가 동기화되었습니다:', new Date().toLocaleTimeString());
            }
        } else {
            console.log('서버 응답 오류:', response.status);
        }
    } catch (error) {
        console.log('동기화 실패:', error);
    }
}

// 데이터 저장
async function saveData() {
    const data = {
        employees,
        teams,
        vacations,
        breakRecords
    };
    
    // 로컬 저장
    localStorage.setItem('dModeData', JSON.stringify(data));
    
    // 서버에 저장
    try {
        const response = await fetch('/api/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success') {
                console.log('서버에 데이터가 저장되었습니다.');
            }
        }
    } catch (error) {
        console.log('서버 저장 실패:', error);
    }
}

// 날짜 포맷팅
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatDateDisplay(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const weekdays = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
    const weekday = weekdays[date.getDay()];
    return `${year}-${month}-${day} (${weekday})`;
}

// 현재 날짜 업데이트
function updateCurrentDate() {
    elements.currentDateDisplay.textContent = formatDateDisplay(currentDate);
}

// 직원 데이터 로드
function loadEmployees() {
    const dateStr = formatDate(currentDate);
    const mmdd = `${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(currentDate.getDate()).padStart(2, '0')}`;
    const weekdays = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
    const dayStr = weekdays[currentDate.getDay()];

    // 휴가 중인 직원 ID들
    const vacationIds = new Set();
    vacations.forEach(vacation => {
        if (vacation.date === mmdd) {
            vacationIds.add(vacation.employeeId);
        }
    });

    // 오늘 근무하는 직원들 필터링
    const workingEmployees = employees.filter(emp => {
        // 휴무일 체크
        if (emp.offDays && emp.offDays.includes(dayStr)) {
            return false;
        }
        // 휴가 체크
        if (vacationIds.has(emp.id)) {
            return false;
        }
        return true;
    });

    // 팀별로 그룹화
    const teamsData = {};
    workingEmployees.forEach(emp => {
        const team = emp.team || '미지정';
        if (!teamsData[team]) {
            teamsData[team] = [];
        }
        
        // 휴식 기록 추가
        const breakRecord = breakRecords.find(br => 
            br.employeeId === emp.id && br.date === dateStr
        );
        
        teamsData[team].push({
            ...emp,
            breakDown: breakRecord ? breakRecord.breakDown : '',
            breakUp: breakRecord ? breakRecord.breakUp : ''
        });
    });

    // UI 업데이트
    renderTeams(teamsData);
}

// 팀 렌더링
function renderTeams(teamsData) {
    elements.teamsContainer.innerHTML = '';
    
    if (Object.keys(teamsData).length === 0) {
        elements.teamsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>오늘 근무하는 직원이 없습니다</h3>
                <p>직원을 추가하거나 날짜를 변경해보세요.</p>
            </div>
        `;
        return;
    }

    Object.keys(teamsData).forEach(teamName => {
        const teamCard = createTeamCard(teamName, teamsData[teamName]);
        elements.teamsContainer.appendChild(teamCard);
    });
}

// 팀 카드 생성
function createTeamCard(teamName, teamEmployees) {
    const teamCard = document.createElement('div');
    teamCard.className = 'team-card';
    
    const teamHeader = document.createElement('div');
    teamHeader.className = 'team-header';
    
    const teamNameEl = document.createElement('h3');
    teamNameEl.className = 'team-name';
    teamNameEl.textContent = teamName;
    teamNameEl.addEventListener('click', () => openAddEmployeeModal(teamName));
    
    const addBtn = document.createElement('button');
    addBtn.className = 'add-employee-btn';
    addBtn.innerHTML = '<i class="fas fa-plus"></i> 직원 추가';
    addBtn.addEventListener('click', () => openAddEmployeeModal(teamName));
    
    teamHeader.appendChild(teamNameEl);
    teamHeader.appendChild(addBtn);
    
    const employeesContainer = document.createElement('div');
    employeesContainer.className = 'employees-container';
    
    teamEmployees.forEach((emp, index) => {
        const employeeCard = createEmployeeCard(emp, teamName, index);
        employeesContainer.appendChild(employeeCard);
    });
    
    teamCard.appendChild(teamHeader);
    teamCard.appendChild(employeesContainer);
    
    return teamCard;
}

// 직원 카드 생성
function createEmployeeCard(employee, teamName, index) {
    const card = document.createElement('div');
    card.className = 'employee-card';
    
    const info = document.createElement('div');
    info.className = 'employee-info';
    
    const name = document.createElement('div');
    name.className = 'employee-name';
    
    const breakInfo = document.createElement('div');
    breakInfo.className = 'break-info';
    
    // 휴식 시간 정보 처리
    const breakDown = employee.breakDown || '';
    const breakUp = employee.breakUp || '';
    
    let timeDiffStr = '';
    let statusText = '';
    
    if (breakDown && breakUp) {
        // 시간 차이 계산
        const downTime = new Date(`2000-01-01T${breakDown}:00`);
        const upTime = new Date(`2000-01-01T${breakUp}:00`);
        const diffMs = upTime - downTime;
        const minutes = Math.floor(diffMs / 60000);
        timeDiffStr = ` [${minutes}분]`;
        statusText = `내려온 시간: ${breakDown}<br>올라온 시간: ${breakUp}`;
    } else if (breakDown && !breakUp) {
        timeDiffStr = ' [밥 먹는중...]';
        statusText = `내려온 시간: ${breakDown}<br>올라온 시간: -`;
    } else {
        statusText = '배고파용 8ㅅ8';
    }
    
    name.innerHTML = `${employee.name}${timeDiffStr}`;
    breakInfo.innerHTML = statusText;
    
    info.appendChild(name);
    info.appendChild(breakInfo);
    
    const actions = document.createElement('div');
    actions.className = 'employee-actions';
    
    const recordBtn = document.createElement('button');
    recordBtn.className = 'action-btn record-btn';
    recordBtn.innerHTML = '⏱️';
    recordBtn.title = '휴식 시간 기록';
    recordBtn.addEventListener('click', () => recordBreakTime(employee.id, teamName, index));
    
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'action-btn cancel-btn';
    cancelBtn.innerHTML = '❌';
    cancelBtn.title = '기록 취소';
    cancelBtn.addEventListener('click', () => cancelBreakTime(employee.id, teamName, index));
    
    actions.appendChild(recordBtn);
    actions.appendChild(cancelBtn);
    
    card.appendChild(info);
    card.appendChild(actions);
    
    return card;
}

// 휴식 시간 기록
function recordBreakTime(employeeId, teamName, index) {
    const currentTime = new Date();
    const timeStr = `${String(currentTime.getHours()).padStart(2, '0')}:${String(currentTime.getMinutes()).padStart(2, '0')}`;
    const dateStr = formatDate(currentDate);
    
    const existingRecord = breakRecords.find(br => 
        br.employeeId === employeeId && br.date === dateStr
    );
    
    if (!existingRecord) {
        // 새 기록 생성
        breakRecords.push({
            id: Date.now(),
            employeeId,
            date: dateStr,
            breakDown: timeStr,
            breakUp: ''
        });
    } else {
        // 기존 기록 업데이트
        if (!existingRecord.breakDown) {
            existingRecord.breakDown = timeStr;
        } else if (!existingRecord.breakUp) {
            existingRecord.breakUp = timeStr;
        } else {
            showMessage('이미 기록이 완료되었습니다.', 'info');
            return;
        }
    }
    
    saveData();
    loadEmployees();
    showMessage('휴식 시간이 기록되었습니다.', 'success');
}

// 휴식 시간 취소
function cancelBreakTime(employeeId, teamName, index) {
    if (!confirm('휴식 시간 기록을 취소하시겠습니까?')) {
        return;
    }
    
    const dateStr = formatDate(currentDate);
    const existingRecord = breakRecords.find(br => 
        br.employeeId === employeeId && br.date === dateStr
    );
    
    if (!existingRecord) {
        showMessage('기록이 없습니다.', 'info');
        return;
    }
    
    if (existingRecord.breakUp) {
        existingRecord.breakUp = '';
    } else if (existingRecord.breakDown) {
        existingRecord.breakDown = '';
    } else {
        showMessage('기록이 없습니다.', 'info');
        return;
    }
    
    saveData();
    loadEmployees();
    showMessage('기록이 취소되었습니다.', 'success');
}

// 메시지 표시
function showMessage(text, type = 'info') {
    // 기존 메시지 제거
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    
    document.querySelector('.main-content').insertBefore(message, elements.teamsContainer);
    
    setTimeout(() => {
        if (message.parentNode) {
            message.remove();
        }
    }, 3000);
}

// 모달 열기/닫기 함수들
function openModal(modal) {
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// 날짜 선택 모달
function openDateModal() {
    elements.dateInput.value = formatDate(currentDate);
    openModal(elements.dateModal);
}

function confirmDate() {
    const selectedDate = new Date(elements.dateInput.value);
    if (selectedDate) {
        currentDate = selectedDate;
        updateCurrentDate();
        loadEmployees();
        closeModal(elements.dateModal);
    }
}

// 직원 추가 모달
function openAddEmployeeModal(teamName = '') {
    elements.employeeName.value = '';
    elements.employeeTeam.value = teamName;
    elements.employeeOffDays.value = '';
    openModal(elements.addEmployeeModal);
}

function saveEmployee() {
    const name = elements.employeeName.value.trim();
    const team = elements.employeeTeam.value.trim();
    const offDays = elements.employeeOffDays.value.trim();
    
    if (!name) {
        showMessage('이름을 입력해주세요.', 'error');
        return;
    }
    
    if (!team) {
        showMessage('팀을 입력해주세요.', 'error');
        return;
    }
    
    const newEmployee = {
        id: Date.now(),
        name,
        team,
        offDays
    };
    
    employees.push(newEmployee);
    
    // 팀 정보도 업데이트
    const existingTeam = teams.find(t => t.name === team);
    if (!existingTeam) {
        teams.push({
            name: team,
            offDays
        });
    } else {
        existingTeam.offDays = offDays;
    }
    
    saveData();
    loadEmployees();
    closeModal(elements.addEmployeeModal);
    showMessage('직원이 등록되었습니다.', 'success');
}

// 직원 수정 모달
function openEditEmployeeModal() {
    // 직원 목록 업데이트
    elements.editEmployeeSelect.innerHTML = '<option value="">직원을 선택하세요</option>';
    employees.forEach(emp => {
        const option = document.createElement('option');
        option.value = emp.id;
        option.textContent = emp.name;
        elements.editEmployeeSelect.appendChild(option);
    });
    
    openModal(elements.editEmployeeModal);
}

function onEditEmployeeSelect() {
    const employeeId = parseInt(elements.editEmployeeSelect.value);
    const employee = employees.find(emp => emp.id === employeeId);
    
    if (employee) {
        elements.editEmployeeName.value = employee.name;
        elements.editEmployeeTeam.value = employee.team;
        elements.editEmployeeOffDays.value = employee.offDays;
    }
}

function updateEmployee() {
    const employeeId = parseInt(elements.editEmployeeSelect.value);
    const employee = employees.find(emp => emp.id === employeeId);
    
    if (!employee) {
        showMessage('직원을 선택해주세요.', 'error');
        return;
    }
    
    const name = elements.editEmployeeName.value.trim();
    const team = elements.editEmployeeTeam.value.trim();
    const offDays = elements.editEmployeeOffDays.value.trim();
    
    if (!name) {
        showMessage('이름을 입력해주세요.', 'error');
        return;
    }
    
    if (!team) {
        showMessage('팀을 입력해주세요.', 'error');
        return;
    }
    
    employee.name = name;
    employee.team = team;
    employee.offDays = offDays;
    
    saveData();
    loadEmployees();
    closeModal(elements.editEmployeeModal);
    showMessage('직원 정보가 수정되었습니다.', 'success');
}

// 직원 삭제 모달
function openDeleteEmployeeModal() {
    // 직원 목록 업데이트
    elements.deleteEmployeeSelect.innerHTML = '<option value="">직원을 선택하세요</option>';
    employees.forEach(emp => {
        const option = document.createElement('option');
        option.value = emp.id;
        option.textContent = emp.name;
        elements.deleteEmployeeSelect.appendChild(option);
    });
    
    openModal(elements.deleteEmployeeModal);
}

function deleteEmployee() {
    const employeeId = parseInt(elements.deleteEmployeeSelect.value);
    const employee = employees.find(emp => emp.id === employeeId);
    
    if (!employee) {
        showMessage('직원을 선택해주세요.', 'error');
        return;
    }
    
    if (!confirm(`정말로 ${employee.name}님을 삭제하시겠습니까?`)) {
        return;
    }
    
    employees = employees.filter(emp => emp.id !== employeeId);
    
    // 관련 데이터도 삭제
    vacations = vacations.filter(vac => vac.employeeId !== employeeId);
    breakRecords = breakRecords.filter(br => br.employeeId !== employeeId);
    
    saveData();
    loadEmployees();
    closeModal(elements.deleteEmployeeModal);
    showMessage('직원이 삭제되었습니다.', 'success');
}

// 팀 수정 모달
function openEditTeamModal() {
    // 팀 목록 업데이트
    elements.editTeamSelect.innerHTML = '<option value="">팀을 선택하세요</option>';
    teams.forEach(team => {
        const option = document.createElement('option');
        option.value = team.name;
        option.textContent = team.name;
        elements.editTeamSelect.appendChild(option);
    });
    
    openModal(elements.editTeamModal);
}

function onEditTeamSelect() {
    const teamName = elements.editTeamSelect.value;
    const team = teams.find(t => t.name === teamName);
    
    if (team) {
        elements.editTeamName.value = team.name;
        elements.editTeamOffDays.value = team.offDays;
    }
}

function updateTeam() {
    const oldTeamName = elements.editTeamSelect.value;
    const team = teams.find(t => t.name === oldTeamName);
    
    if (!team) {
        showMessage('팀을 선택해주세요.', 'error');
        return;
    }
    
    const newTeamName = elements.editTeamName.value.trim();
    const newOffDays = elements.editTeamOffDays.value.trim();
    
    if (!newTeamName) {
        showMessage('새 팀 이름을 입력해주세요.', 'error');
        return;
    }
    
    // 팀 이름이 변경된 경우
    if (oldTeamName !== newTeamName) {
        // 이미 존재하는 팀 이름인지 확인
        const existingTeam = teams.find(t => t.name === newTeamName);
        if (existingTeam) {
            showMessage('이미 존재하는 팀 이름입니다.', 'error');
            return;
        }
        
        // 직원들의 팀 정보 업데이트
        employees.forEach(emp => {
            if (emp.team === oldTeamName) {
                emp.team = newTeamName;
            }
        });
    }
    
    // 팀 정보 업데이트
    team.name = newTeamName;
    team.offDays = newOffDays;
    
    saveData();
    loadEmployees();
    closeModal(elements.editTeamModal);
    showMessage('팀 정보가 수정되었습니다.', 'success');
}

// 휴가 등록 모달
function openAddVacationModal() {
    // 직원 목록 업데이트
    elements.vacationEmployeeSelect.innerHTML = '<option value="">직원을 선택하세요</option>';
    employees.forEach(emp => {
        const option = document.createElement('option');
        option.value = emp.id;
        option.textContent = emp.name;
        elements.vacationEmployeeSelect.appendChild(option);
    });
    
    elements.vacationDate.value = formatDate(currentDate);
    openModal(elements.addVacationModal);
}

function saveVacation() {
    const employeeId = parseInt(elements.vacationEmployeeSelect.value);
    const vacationDate = elements.vacationDate.value;
    
    if (!employeeId) {
        showMessage('직원을 선택해주세요.', 'error');
        return;
    }
    
    if (!vacationDate) {
        showMessage('휴가 날짜를 선택해주세요.', 'error');
        return;
    }
    
    const date = new Date(vacationDate);
    const mmdd = `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    
    // 중복 확인
    const existingVacation = vacations.find(vac => 
        vac.employeeId === employeeId && vac.date === mmdd
    );
    
    if (existingVacation) {
        showMessage('이미 등록된 휴가입니다.', 'error');
        return;
    }
    
    const employee = employees.find(emp => emp.id === employeeId);
    vacations.push({
        id: Date.now(),
        employeeId,
        date: mmdd
    });
    
    saveData();
    loadEmployees();
    closeModal(elements.addVacationModal);
    showMessage(`${employee.name}님의 휴가가 등록되었습니다.`, 'success');
}

// 휴가 취소 모달
function openCancelVacationModal() {
    // 휴가 목록 업데이트
    elements.cancelVacationSelect.innerHTML = '<option value="">휴가를 선택하세요</option>';
    vacations.forEach(vacation => {
        const employee = employees.find(emp => emp.id === vacation.employeeId);
        if (employee) {
            const option = document.createElement('option');
            option.value = vacation.id;
            option.textContent = `${employee.name} [${vacation.date}]`;
            elements.cancelVacationSelect.appendChild(option);
        }
    });
    
    openModal(elements.cancelVacationModal);
}

function cancelVacation() {
    const vacationId = parseInt(elements.cancelVacationSelect.value);
    const vacation = vacations.find(vac => vac.id === vacationId);
    
    if (!vacation) {
        showMessage('휴가를 선택해주세요.', 'error');
        return;
    }
    
    const employee = employees.find(emp => emp.id === vacation.employeeId);
    vacations = vacations.filter(vac => vac.id !== vacationId);
    
    saveData();
    loadEmployees();
    closeModal(elements.cancelVacationModal);
    showMessage(`${employee.name}님의 휴가가 취소되었습니다.`, 'success');
}

// 관리자 모드
function openAdminModal() {
    openPasswordModal(() => {
        // 비밀번호 확인 후 관리자 모드 열기
        elements.adminEmployeeSelect.innerHTML = '<option value="">직원을 선택하세요</option>';
        employees.forEach(emp => {
            const option = document.createElement('option');
            option.value = emp.id;
            option.textContent = emp.name;
            elements.adminEmployeeSelect.appendChild(option);
        });
        
        elements.adminDate.value = formatDate(currentDate);
        elements.adminBreakDown.value = '';
        elements.adminBreakUp.value = '';
        
        closeModal(elements.passwordModal);
        openModal(elements.adminModal);
    });
}

function openPasswordModal(callback) {
    elements.passwordInput.value = '';
    openModal(elements.passwordModal);
    
    const confirmPassword = () => {
        if (elements.passwordInput.value === '1212') {
            callback();
        } else {
            showMessage('비밀번호가 틀렸습니다.', 'error');
        }
    };
    
    elements.passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            confirmPassword();
        }
    });
    
    document.getElementById('confirm-password').onclick = confirmPassword;
}

function saveAdminRecord() {
    const employeeId = parseInt(elements.adminEmployeeSelect.value);
    const date = elements.adminDate.value;
    const breakDown = elements.adminBreakDown.value;
    const breakUp = elements.adminBreakUp.value;
    
    if (!employeeId) {
        showMessage('직원을 선택해주세요.', 'error');
        return;
    }
    
    if (!date) {
        showMessage('날짜를 선택해주세요.', 'error');
        return;
    }
    
    const existingRecord = breakRecords.find(br => 
        br.employeeId === employeeId && br.date === date
    );
    
    if (existingRecord) {
        existingRecord.breakDown = breakDown;
        existingRecord.breakUp = breakUp;
    } else {
        breakRecords.push({
            id: Date.now(),
            employeeId,
            date,
            breakDown,
            breakUp
        });
    }
    
    saveData();
    loadEmployees();
    closeModal(elements.adminModal);
    showMessage('기록이 저장되었습니다.', 'success');
}

// 햄버거 메뉴 관련 함수들
function openHamburgerMenu() {
    elements.hamburgerMenu.classList.add('active');
    elements.hamburgerBtn.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeHamburgerMenu() {
    elements.hamburgerMenu.classList.remove('active');
    elements.hamburgerBtn.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// 이벤트 리스너 등록
function setupEventListeners() {
    // 햄버거 메뉴
    elements.hamburgerBtn.addEventListener('click', openHamburgerMenu);
    elements.closeMenuBtn.addEventListener('click', closeHamburgerMenu);
    elements.menuOverlay.addEventListener('click', closeHamburgerMenu);
    
    // 날짜 선택
    elements.datePickerBtn.addEventListener('click', openDateModal);
    elements.currentDateDisplay.addEventListener('click', openDateModal);
    document.getElementById('confirm-date').addEventListener('click', confirmDate);
    
    // 직원 관리
    document.getElementById('add-junior-btn').addEventListener('click', () => {
        closeHamburgerMenu();
        openAddEmployeeModal();
    });
    document.getElementById('add-designer-btn').addEventListener('click', () => {
        closeHamburgerMenu();
        openAddEmployeeModal();
    });
    document.getElementById('edit-employee-btn').addEventListener('click', () => {
        closeHamburgerMenu();
        openEditEmployeeModal();
    });
    document.getElementById('delete-employee-btn').addEventListener('click', () => {
        closeHamburgerMenu();
        openDeleteEmployeeModal();
    });
    document.getElementById('edit-team-btn').addEventListener('click', () => {
        closeHamburgerMenu();
        openEditTeamModal();
    });
    
    // 휴가 관리
    document.getElementById('add-vacation-btn').addEventListener('click', () => {
        closeHamburgerMenu();
        openAddVacationModal();
    });
    document.getElementById('cancel-vacation-btn').addEventListener('click', () => {
        closeHamburgerMenu();
        openCancelVacationModal();
    });
    
    // 관리자
    document.getElementById('admin-btn').addEventListener('click', () => {
        closeHamburgerMenu();
        openAdminModal();
    });
    
    // 폼 제출
    document.getElementById('save-employee').addEventListener('click', saveEmployee);
    document.getElementById('update-employee').addEventListener('click', updateEmployee);
    document.getElementById('confirm-delete-employee').addEventListener('click', deleteEmployee);
    document.getElementById('update-team').addEventListener('click', updateTeam);
    document.getElementById('save-vacation').addEventListener('click', saveVacation);
    document.getElementById('confirm-cancel-vacation').addEventListener('click', cancelVacation);
    document.getElementById('save-admin-record').addEventListener('click', saveAdminRecord);
    
    // 선택 변경 이벤트
    elements.editEmployeeSelect.addEventListener('change', onEditEmployeeSelect);
    elements.editTeamSelect.addEventListener('change', onEditTeamSelect);
    
    // 모달 닫기
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            closeModal(modal);
        });
    });
    
    // 모달 외부 클릭 시 닫기
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });
}

// 앱 초기화
async function initApp() {
    await initDatabase();
    updateCurrentDate();
    setupEventListeners();
}

// 페이지 로드 시 앱 초기화
document.addEventListener('DOMContentLoaded', initApp);

// 새로고침 시 데이터 강제 로드
window.addEventListener('load', async function() {
    console.log('페이지 로드 완료 - 데이터 강제 로드');
    await loadDataFromServer();
});

// 페이지 포커스 시 데이터 동기화
window.addEventListener('focus', async function() {
    console.log('페이지 포커스 - 데이터 동기화');
    await syncWithServer();
});
