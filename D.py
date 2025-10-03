import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.simpledialog import askstring
import sqlite3
from datetime import datetime
import os
import ctypes
import sys
import atexit
import errno

TEAM_FRAME_WIDTH = 210
EMP_FRAME_WIDTH = 200
EMP_FRAME_HEIGHT = 50

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # 직원 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            team TEXT,
            off_days TEXT
        )
    ''')
    # 팀 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            team TEXT PRIMARY KEY,
            off_days TEXT
        )
    ''')
    # 휴가 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS vacations (
            employee_id INTEGER,
            vacation_date TEXT,
            UNIQUE(employee_id, vacation_date)
        )
    ''')
    # 날짜별 break 기록 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS break_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            record_date TEXT,
            break_down TEXT,
            break_up TEXT,
            UNIQUE(employee_id, record_date)
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

class FlowFrame(ttk.Frame):
    def __init__(self, master, child_width=320, **kwargs):
        super().__init__(master, **kwargs)
        self.child_width = child_width
        self.bind("<Configure>", self.on_configure)

    def on_configure(self, event):
        width = self.winfo_width()
        cols = max(1, width // self.child_width)
        for i, child in enumerate(self.winfo_children()):
            child.grid_forget()
            child.grid(row=i // cols, column=i % cols, padx=5, pady=5, sticky="nsew")

class TeamFrame(tk.Frame):
    def __init__(self, master, team, emp_list, left_click_callback, right_click_callback, add_employee_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.team = team
        self.emp_list = emp_list
        self.left_click_callback = left_click_callback
        self.right_click_callback = right_click_callback
        self.add_employee_callback = add_employee_callback

        self.config(width=TEAM_FRAME_WIDTH, bg="SystemButtonFace", bd=0, relief="flat")
        self.header = tk.Label(
            self, text=self.team, anchor="w",
            font=("TkDefaultFont", 12, "bold"),
            bg=self["bg"], padx=5, pady=5, cursor="hand2"
        )
        self.header.pack(fill=tk.X)
        # 헤더 클릭 시 → 해당 팀에 새 직원 등록
        self.header.bind("<Button-1>", lambda e: self.add_employee_callback(self.team))

        self.container = tk.Frame(self, bg=self["bg"])
        self.container.pack(fill=tk.BOTH, expand=True)
        self.load_employees()

    def load_employees(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        for index, emp in enumerate(self.emp_list):
            break_down = emp.get('break_down', "") or "-"
            break_up = emp.get('break_up', "") or ""
            if break_down != "-" and break_up:
                try:
                    fmt = "%H:%M"
                    down_dt = datetime.strptime(break_down, fmt)
                    up_dt = datetime.strptime(break_up, fmt)
                    diff = up_dt - down_dt
                    minutes = int(diff.total_seconds() / 60)
                    time_diff_str = f" [{minutes}분]"
                except ValueError:
                    time_diff_str = ""
            elif break_down != "-" and not break_up:
                time_diff_str = " [밥 먹는중...]"
            else:
                time_diff_str = ""

            name_line = f"{emp['name']}{time_diff_str}"
            if break_down == "-" and break_up == "":
                display_text = f"{name_line}\n배고파용 8ㅅ8"
            else:
                display_text = (
                    f"{name_line}\n"
                    f"내려온 시간: {break_down}\n"
                    f"올라온 시간: {break_up or '-'}"
                )

            emp_frame = tk.Frame(
                self.container, width=EMP_FRAME_WIDTH, height=EMP_FRAME_HEIGHT,
                bg="white", bd=1, relief="flat"
            )
            emp_frame.pack_propagate(False)
            emp_frame.pack(fill=tk.X, pady=5)

            emp_label = tk.Label(
                emp_frame, text=display_text, bg="white",
                anchor="nw", justify=tk.LEFT, padx=10
            )
            emp_label.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            emp_label.config(cursor="arrow")

            # 버튼 프레임 추가
            btn_frame = tk.Frame(emp_frame, bg="white")
            btn_frame.pack(side=tk.RIGHT, padx=5, pady=5)

            # 기록 버튼
            record_btn = tk.Button(
                btn_frame, text="⏱︎", width=2, relief="ridge",
                command=lambda i=index: self.left_click_callback(i)
            )
            record_btn.pack(side=tk.LEFT, padx=2)

            # 취소 버튼
            def cancel_with_confirm(i=index):
                emp = self.emp_list[i]
                if messagebox.askyesno("확인", f"{emp['name']}님의 시간 기록을 취소하시겠습니까?"):
                    self.right_click_callback(i)
            cancel_btn = tk.Button(
                btn_frame, text="❌", width=2, relief="ridge",
                command=cancel_with_confirm
            )
            cancel_btn.pack(side=tk.LEFT, padx=2)

            # Hover 시 배경색 변화
            emp_frame.bind("<Enter>", lambda event, frame=emp_frame: self.animate_bg(frame, (255,255,255), (217,217,217)))
            emp_frame.bind("<Leave>", lambda event, frame=emp_frame: self.restore_bg(frame))
            emp_label.bind("<Enter>", lambda event, frame=emp_frame: self.animate_bg(frame, (255,255,255), (217,217,217)))
            emp_label.bind("<Leave>", lambda event, frame=emp_frame: self.restore_bg(frame))

    def animate_bg(self, widget, start_rgb, end_rgb, step=0, steps=10, delay=30):
        if hasattr(widget, '_anim_after_id'):
            try:
                widget.after_cancel(widget._anim_after_id)
            except Exception:
                pass
            widget._anim_after_id = None

        if step > steps:
            return
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * step / steps)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * step / steps)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * step / steps)
        new_color = f"#{r:02x}{g:02x}{b:02x}"
        widget.config(bg=new_color)
        for child in widget.winfo_children():
            try:
                child.config(bg=new_color)
            except Exception:
                pass

        widget._anim_after_id = widget.after(delay, 
            lambda: self.animate_bg(widget, start_rgb, end_rgb, step+1, steps, delay))

    def restore_bg(self, widget):
        if hasattr(widget, '_anim_after_id'):
            try:
                widget.after_cancel(widget._anim_after_id)
            except Exception:
                pass
            widget._anim_after_id = None
        widget.config(bg="#ffffff")
        for child in widget.winfo_children():
            try:
                child.config(bg="#ffffff")
            except Exception:
                pass

class EmployeeManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("차홍룸 노원점 D모드 관리")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # 종료 시 비밀번호 입력 요구
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(0, self.hide_from_taskbar)

        self.current_date = datetime.now().date()

        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.date_label = ttk.Label(self.top_frame, font=("TkDefaultFont", 12, "bold"), cursor="hand2")
        self.date_label.pack(side=tk.LEFT, padx=10, pady=5)
        self.date_label.bind("<Button-1>", lambda e: self.open_calendar_window())

        menubar = tk.Menu(self)
        # 직원관리 메뉴
        employee_menu = tk.Menu(menubar, tearoff=0)
        employee_menu.add_command(label="주니어 추가", command=self.open_junior_add_employee_window)
        employee_menu.add_command(label="디자이너 추가", command=self.open_designer_team_window)
        employee_menu.add_command(label="직원 수정", command=self.open_update_employee_window)
        employee_menu.add_command(label="직원 삭제", command=self.open_delete_employee_window)
        # 팀 수정 메뉴 추가
        employee_menu.add_command(label="팀 수정", command=self.open_update_team_window)
        menubar.add_cascade(label="직원관리", menu=employee_menu)

        # 휴가관리 메뉴
        vacation_menu = tk.Menu(menubar, tearoff=0)
        vacation_menu.add_command(label="휴가 등록", command=self.open_vacation_window)
        self.vacation_cancel_menu = tk.Menu(vacation_menu, tearoff=0)
        vacation_menu.add_cascade(label="휴가 취소", menu=self.vacation_cancel_menu)
        menubar.add_cascade(label="휴가관리", menu=vacation_menu)

        # 관리자 메뉴
        admin_menu = tk.Menu(menubar, tearoff=0)
        admin_menu.add_command(label="관리자 모드", command=self.open_admin_window)
        menubar.add_cascade(label="관리자", menu=admin_menu)

        self.config(menu=menubar)

        self.flow = FlowFrame(self, child_width=TEAM_FRAME_WIDTH, padding=10)
        self.flow.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.employee_data = []
        self.team_frames = {}
        self.selected_employee = None

        self.update_date_label()
        self.load_employees()
        self.update_vacation_cancel_menu()

    def on_close(self):
        pwd = askstring("종료 확인", "종료 비밀번호를 입력하세요:", show="*")
        if pwd == "1212":
            self.destroy()
        else:
            messagebox.showerror("오류", "비밀번호가 틀렸습니다.")

    def hide_from_taskbar(self):
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        hwnd = self.winfo_id()
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_APPWINDOW
        style = style | WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020
        flags = SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED
        ctypes.windll.user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, flags)

        self.withdraw()
        self.after(10, self.deiconify)

    def update_date_label(self):
        date_str = self.current_date.strftime("%Y-%m-%d")
        weekday_map = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        day_str = weekday_map[self.current_date.weekday()]
        self.date_label.config(text=f"{date_str} ({day_str})")

    def open_calendar_window(self):
        from tkcalendar import Calendar
        win = tk.Toplevel(self)
        win.title("날짜 선택")
        win.geometry("400x400")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="날짜를 선택하세요.").pack(pady=5)
        cal = Calendar(frame, selectmode="day", date_pattern="yyyy-mm-dd",
                       firstweekday="sunday", locale="ko_KR")
        cal.pack(pady=5, fill=tk.BOTH, expand=True)
        cal.selection_set(self.current_date)

        def on_confirm():
            selected_date = cal.selection_get()
            if not selected_date:
                messagebox.showerror("오류", "날짜를 선택하세요.")
                return
            self.current_date = selected_date
            self.update_date_label()
            win.destroy()
            self.load_employees()

        ttk.Button(frame, text="확인", command=on_confirm).pack(pady=10)

    def load_employees(self):
        conn = get_db_connection()
        employees = conn.execute('SELECT * FROM employees').fetchall()
        rows = conn.execute('SELECT employee_id, vacation_date FROM vacations').fetchall()

        date_str = self.current_date.strftime("%Y-%m-%d")
        vac_mm_dd = self.current_date.strftime("%m-%d")
        weekday_map = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        day_str = weekday_map[self.current_date.weekday()]

        vacation_ids = {r['employee_id'] for r in rows if r['vacation_date'] == vac_mm_dd}

        working_employees = []
        for emp in employees:
            off_days = emp['off_days']
            if off_days and day_str in off_days:
                continue
            if emp['id'] in vacation_ids:
                continue
            working_employees.append(emp)

        emp_dicts = []
        for emp in working_employees:
            emp_data = {
                'id': emp['id'],
                'name': emp['name'],
                'team': emp['team'],
                'off_days': emp['off_days'],
                'break_down': "",
                'break_up': ""
            }
            br = conn.execute('''
                SELECT break_down, break_up
                FROM break_records
                WHERE employee_id=? AND record_date=?
            ''', (emp['id'], date_str)).fetchone()
            if br:
                emp_data['break_down'] = br['break_down'] or ""
                emp_data['break_up'] = br['break_up'] or ""
            emp_dicts.append(emp_data)
        conn.close()

        self.employee_data = emp_dicts

        groups = {}
        for emp_data in emp_dicts:
            team = emp_data['team'].strip() if emp_data['team'] else "미지정"
            groups.setdefault(team, []).append(emp_data)

        for widget in self.flow.winfo_children():
            widget.destroy()

        self.team_frames = {}
        for team, emp_list in groups.items():
            tf = TeamFrame(
                self.flow, team, emp_list,
                left_click_callback=lambda i, tm=team: self.record_break_time(tm, i),
                right_click_callback=lambda i, tm=team: self.cancel_break_time(tm, i),
                add_employee_callback=self.open_add_employee_window_for_team
            )
            self.team_frames[team] = tf
            tf.grid()
        self.flow.on_configure(None)

    def record_break_time(self, team, index):
        emp = self.get_employee(team, index)
        if not emp:
            return
        current_time = datetime.now().strftime('%H:%M')
        date_str = self.current_date.strftime("%Y-%m-%d")

        conn = get_db_connection()
        row = conn.execute('''
            SELECT break_down, break_up
            FROM break_records
            WHERE employee_id=? AND record_date=?
        ''', (emp['id'], date_str)).fetchone()

        if row is None:
            conn.execute('''
                INSERT INTO break_records (employee_id, record_date, break_down, break_up)
                VALUES (?, ?, ?, ?)
            ''', (emp['id'], date_str, current_time, ""))
        else:
            break_down = row['break_down']
            break_up = row['break_up']
            if not break_down:
                conn.execute('''
                    UPDATE break_records
                    SET break_down=?
                    WHERE employee_id=? AND record_date=?
                ''', (current_time, emp['id'], date_str))
            elif not break_up:
                conn.execute('''
                    UPDATE break_records
                    SET break_up=?
                    WHERE employee_id=? AND record_date=?
                ''', (current_time, emp['id'], date_str))
            else:
                messagebox.showinfo("안내", f"'{emp['name']}'님의 기록이 이미 완료되었습니다.")

        conn.commit()
        conn.close()
        self.load_employees()

    def cancel_break_time(self, team, index):
        emp = self.get_employee(team, index)
        if not emp:
            return
        date_str = self.current_date.strftime("%Y-%m-%d")

        conn = get_db_connection()
        row = conn.execute('''
            SELECT break_down, break_up
            FROM break_records
            WHERE employee_id=? AND record_date=?
        ''', (emp['id'], date_str)).fetchone()

        if row is None:
            messagebox.showinfo("안내", f"'{emp['name']}'님의 기록이 없습니다.")
        else:
            break_down = row['break_down']
            break_up = row['break_up']
            if break_up:
                conn.execute('''
                    UPDATE break_records
                    SET break_up=''
                    WHERE employee_id=? AND record_date=?
                ''', (emp['id'], date_str))
            elif break_down:
                conn.execute('''
                    UPDATE break_records
                    SET break_down=''
                    WHERE employee_id=? AND record_date=?
                ''', (emp['id'], date_str))
            else:
                messagebox.showinfo("안내", f"'{emp['name']}'님의 기록이 없습니다.")

        conn.commit()
        conn.close()
        self.load_employees()

    def get_employee(self, team, index):
        groups = {}
        for emp_data in self.employee_data:
            t = emp_data['team'].strip() if emp_data['team'] else "미지정"
            groups.setdefault(t, []).append(emp_data)
        if team in groups and index < len(groups[team]):
            return groups[team][index]
        return None

    # -------------------- [직원 수정 / 삭제] --------------------
    def open_update_employee_window(self):
        win = tk.Toplevel(self)
        win.title("직원 수정")
        win.geometry("400x300")
        win.resizable(False, False)
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="수정할 직원을 선택하세요.").pack(pady=5)
        conn = get_db_connection()
        all_employees = conn.execute("SELECT * FROM employees").fetchall()
        conn.close()
        employee_names = [emp['name'] for emp in all_employees]
        employee_var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=employee_var, values=employee_names, state="readonly")
        combo.pack(fill=tk.X, padx=10)

        ttk.Label(frame, text="이름").pack(pady=5)
        name_entry = ttk.Entry(frame)
        name_entry.pack(fill=tk.X, padx=10)

        ttk.Label(frame, text="팀").pack(pady=5)
        team_entry = ttk.Entry(frame)
        team_entry.pack(fill=tk.X, padx=10)

        ttk.Label(frame, text="휴무").pack(pady=5)
        off_entry = ttk.Entry(frame)
        off_entry.pack(fill=tk.X, padx=10)

        def on_select(event):
            selected_name = employee_var.get()
            for emp in all_employees:
                if emp['name'] == selected_name:
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, emp['name'])
                    team_entry.delete(0, tk.END)
                    team_entry.insert(0, emp['team'] if emp['team'] else "")
                    off_entry.delete(0, tk.END)
                    off_entry.insert(0, emp['off_days'] if emp['off_days'] else "")
                    employee_var.employee_id = emp['id']
                    break

        combo.bind("<<ComboboxSelected>>", on_select)

        def update_employee():
            if not hasattr(employee_var, "employee_id"):
                messagebox.showwarning("선택 필요", "수정할 직원을 선택해 주세요.")
                return
            new_name = name_entry.get().strip()
            new_team = team_entry.get().strip()
            off_days = off_entry.get().strip()
            emp_id = employee_var.employee_id
            conn = get_db_connection()
            conn.execute("UPDATE employees SET name=?, team=?, off_days=? WHERE id=?",
                         (new_name, new_team, off_days, emp_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", "직원 수정이 완료되었습니다.")
            win.destroy()
            self.load_employees()

        update_btn = ttk.Button(frame, text="직원 수정", command=update_employee)
        update_btn.pack(pady=10)

    def open_delete_employee_window(self):
        win = tk.Toplevel(self)
        win.title("직원 삭제")
        win.geometry("400x200")
        win.resizable(False, False)
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="삭제할 직원을 선택하세요.").pack(pady=5)
        conn = get_db_connection()
        all_employees = conn.execute("SELECT * FROM employees").fetchall()
        conn.close()
        employee_names = [emp['name'] for emp in all_employees]
        employee_var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=employee_var, values=employee_names, state="readonly")
        combo.pack(fill=tk.X, padx=10)

        def on_select(event):
            selected_name = employee_var.get()
            for emp in all_employees:
                if emp['name'] == selected_name:
                    employee_var.employee_id = emp['id']
                    break

        combo.bind("<<ComboboxSelected>>", on_select)

        def delete_employee():
            if not hasattr(employee_var, "employee_id"):
                messagebox.showwarning("선택 필요", "삭제할 직원을 선택해 주세요.")
                return
            if not messagebox.askyesno("확인", "정말 삭제하시겠습니까?"):
                return
            emp_id = employee_var.employee_id
            conn = get_db_connection()
            conn.execute("DELETE FROM employees WHERE id=?", (emp_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", "직원 삭제가 완료되었습니다.")
            win.destroy()
            self.load_employees()

        delete_btn = ttk.Button(frame, text="직원 삭제", command=delete_employee)
        delete_btn.pack(pady=10)

    # -------------------- [팀 수정] --------------------
    def open_update_team_window(self):
        win = tk.Toplevel(self)
        win.title("팀 수정")
        win.geometry("400x250")
        win.resizable(False, False)
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="수정할 팀을 선택하세요.").pack(pady=5)

        conn = get_db_connection()
        all_teams = conn.execute("SELECT * FROM teams").fetchall()
        conn.close()

        team_names = [t['team'] for t in all_teams]
        team_var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=team_var, values=team_names, state="readonly")
        combo.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frame, text="새 팀 이름").pack(pady=5)
        new_team_entry = ttk.Entry(frame)
        new_team_entry.pack(fill=tk.X, padx=10)

        ttk.Label(frame, text="휴무").pack(pady=5)
        off_entry = ttk.Entry(frame)
        off_entry.pack(fill=tk.X, padx=10)

        def on_select(event):
            selected_team = team_var.get()
            for t in all_teams:
                if t['team'] == selected_team:
                    new_team_entry.delete(0, tk.END)
                    new_team_entry.insert(0, t['team'])
                    off_entry.delete(0, tk.END)
                    off_entry.insert(0, t['off_days'] if t['off_days'] else "")
                    break

        combo.bind("<<ComboboxSelected>>", on_select)

        def update_team():
            old_team = team_var.get().strip()
            if not old_team:
                messagebox.showwarning("주의", "수정할 팀을 먼저 선택하세요.")
                return
            new_team = new_team_entry.get().strip()
            new_off = off_entry.get().strip()
            if not new_team:
                messagebox.showwarning("주의", "새 팀 이름은 필수입니다.")
                return

            conn = get_db_connection()
            c = conn.cursor()
            try:
                c.execute("BEGIN")
                # employees 테이블에서 old_team -> new_team
                c.execute("UPDATE employees SET team=? WHERE team=?", (new_team, old_team))

                # 이미 존재하는 팀 이름이면 충돌 발생 가능
                conflict = c.execute("SELECT team FROM teams WHERE team=?", (new_team,)).fetchone()
                if conflict and new_team != old_team:
                    messagebox.showerror("오류", f"이미 존재하는 팀 이름입니다: {new_team}")
                    c.execute("ROLLBACK")
                    conn.close()
                    return

                # teams 테이블에서 old_team -> new_team, off_days 업데이트
                c.execute("UPDATE teams SET team=?, off_days=? WHERE team=?", (new_team, new_off, old_team))

                c.execute("COMMIT")
                messagebox.showinfo("성공", "팀 정보가 수정되었습니다.")
            except Exception as e:
                c.execute("ROLLBACK")
                messagebox.showerror("오류", str(e))
            finally:
                conn.close()

            win.destroy()
            self.load_employees()

        ttk.Button(frame, text="수정", command=update_team).pack(pady=10)

    # -------------------- [직원 등록] --------------------
    def open_add_employee_window_for_team(self, team):
        off_days = self.get_team_off_days(team)
        add_win = tk.Toplevel(self)
        add_win.title("신규 직원 등록")
        add_win.geometry("400x300")
        add_win.resizable(False, False)
        add_frame = ttk.Frame(add_win, padding=10)
        add_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(add_win, text="이름").pack(pady=5)
        name_entry = ttk.Entry(add_win)
        name_entry.pack(fill=tk.X, padx=10)

        ttk.Label(add_win, text="팀").pack(pady=5)
        team_entry = ttk.Entry(add_win)
        team_entry.pack(fill=tk.X, padx=10)
        team_entry.insert(0, team)
        team_entry.config(state="readonly")

        ttk.Label(add_win, text="휴무").pack(pady=5)
        off_entry = ttk.Entry(add_win)
        off_entry.pack(fill=tk.X, padx=10)
        off_entry.insert(0, off_days)

        def add_employee():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("오류", "이름은 필수입니다.")
                return
            off_days_val = off_entry.get().strip()
            conn = get_db_connection()
            # 팀 테이블도 갱신
            conn.execute('INSERT OR REPLACE INTO teams (team, off_days) VALUES (?, ?)', (team, off_days_val))
            conn.execute('INSERT INTO employees (name, team, off_days) VALUES (?, ?, ?)', (name, team, off_days_val))
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", "직원 등록이 완료되었습니다.")
            add_win.destroy()
            self.load_employees()

        register_btn = ttk.Button(add_win, text="등록", command=add_employee)
        register_btn.pack(pady=10)

    def get_team_off_days(self, team):
        conn = get_db_connection()
        row = conn.execute('SELECT off_days FROM teams WHERE team=?', (team,)).fetchone()
        conn.close()
        if row:
            return row['off_days']
        return ""

    # -------------------- [주니어/디자이너 등록] --------------------
    def get_designer_teams(self):
        conn = get_db_connection()
        rows = conn.execute('SELECT team FROM teams').fetchall()
        conn.close()
        return [row['team'] for row in rows]

    def open_junior_add_employee_window(self):
        add_win = tk.Toplevel(self)
        add_win.title("주니어 추가")
        add_win.geometry("400x300")
        add_win.resizable(False, False)
        add_frame = ttk.Frame(add_win, padding=10)
        add_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(add_win, text="이름").pack(pady=5)
        name_entry = ttk.Entry(add_win)
        name_entry.pack(fill=tk.X, padx=10)

        ttk.Label(add_win, text="디자이너 팀").pack(pady=5)
        designer_teams = self.get_designer_teams()
        team_var = tk.StringVar()
        team_combo = ttk.Combobox(add_win, textvariable=team_var, values=designer_teams, state="readonly")
        team_combo.pack(fill=tk.X, padx=10)

        ttk.Label(add_win, text="휴무").pack(pady=5)
        off_entry = ttk.Entry(add_win)
        off_entry.pack(fill=tk.X, padx=10)

        def on_team_select(event):
            selected_team = team_var.get()
            off_entry.delete(0, tk.END)
            off_entry.insert(0, self.get_team_off_days(selected_team))
        team_combo.bind("<<ComboboxSelected>>", on_team_select)

        def add_employee():
            name = name_entry.get().strip()
            team_val = team_var.get()
            off_days_val = off_entry.get().strip()
            if not name:
                messagebox.showerror("오류", "이름은 필수입니다.")
                return
            if not team_val:
                messagebox.showerror("오류", "디자이너 팀을 선택해 주세요.")
                return
            conn = get_db_connection()
            conn.execute('INSERT INTO employees (name, team, off_days) VALUES (?, ?, ?)', (name, team_val, off_days_val))
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", "직원 등록이 완료되었습니다.")
            add_win.destroy()
            self.load_employees()

        register_btn = ttk.Button(add_win, text="등록", command=add_employee)
        register_btn.pack(pady=10)

    def open_designer_team_window(self):
        add_win = tk.Toplevel(self)
        add_win.title("디자이너 추가")
        add_win.geometry("400x250")
        add_win.resizable(False, False)
        add_frame = ttk.Frame(add_win, padding=10)
        add_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(add_win, text="디자이너 팀").pack(pady=5)
        team_entry = ttk.Entry(add_win)
        team_entry.pack(fill=tk.X, padx=10)

        ttk.Label(add_win, text="휴무").pack(pady=5)
        off_entry = ttk.Entry(add_win)
        off_entry.pack(fill=tk.X, padx=10)

        def add_team():
            team = team_entry.get().strip()
            off_days = off_entry.get().strip()
            if not team:
                messagebox.showerror("오류", "디자이너 팀은 필수입니다.")
                return
            conn = get_db_connection()
            conn.execute('INSERT OR REPLACE INTO teams (team, off_days) VALUES (?, ?)', (team, off_days))
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", "디자이너 팀이 추가되었습니다.")
            add_win.destroy()

        register_btn = ttk.Button(add_win, text="추가", command=add_team)
        register_btn.pack(pady=10)

    # -------------------- [휴가 등록 / 취소] --------------------
    def open_vacation_window(self):
        from tkcalendar import Calendar
        win = tk.Toplevel(self)
        win.title("휴가 등록")
        win.geometry("400x400")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="직원명:").pack(pady=5)
        name_entry = ttk.Entry(frame)
        name_entry.pack(pady=5)

        ttk.Label(frame, text="휴가 날짜 (단일 선택)").pack(pady=5)
        cal = Calendar(frame, selectmode="day", date_pattern="yyyy-mm-dd", firstweekday="sunday", locale="ko_KR")
        cal.pack(pady=5, fill=tk.BOTH, expand=True)

        def submit_vacation():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("오류", "직원명을 입력하세요.")
                return
            selected_date = cal.selection_get()
            if not selected_date:
                messagebox.showerror("오류", "날짜를 선택하세요.")
                return
            vac_date_str = selected_date.strftime("%m-%d")
            conn = get_db_connection()
            row = conn.execute("SELECT id FROM employees WHERE name = ?", (name,)).fetchone()
            if not row:
                messagebox.showerror("오류", f"'{name}' 직원이 존재하지 않습니다.")
                conn.close()
                return
            employee_id = row['id']
            conn.execute(
                "INSERT OR IGNORE INTO vacations (employee_id, vacation_date) VALUES (?, ?)",
                (employee_id, vac_date_str)
            )
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", f"'{name}'님의 휴가({vac_date_str})가 등록되었습니다.")
            win.destroy()
            self.load_employees()
            self.update_vacation_cancel_menu()

        ttk.Button(frame, text="확인", command=submit_vacation).pack(pady=10)

    def update_vacation_cancel_menu(self):
        self.vacation_cancel_menu.delete(0, tk.END)
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT v.employee_id, v.vacation_date, e.name 
            FROM vacations v JOIN employees e ON v.employee_id = e.id
        ''').fetchall()
        conn.close()
        if not rows:
            self.vacation_cancel_menu.add_command(label="등록된 휴가 없음", state="disabled")
        else:
            for row in rows:
                label = f"{row['name']}[{row['vacation_date']}]"
                self.vacation_cancel_menu.add_command(
                    label=label,
                    command=lambda r=row: self.cancel_vacation(r['employee_id'], r['vacation_date'])
                )

    def cancel_vacation(self, employee_id, vacation_date):
        conn = get_db_connection()
        conn.execute("DELETE FROM vacations WHERE employee_id=? AND vacation_date=?", (employee_id, vacation_date))
        conn.commit()
        conn.close()
        messagebox.showinfo("휴가 취소", f"휴가 {vacation_date}가 취소되었습니다.")
        self.load_employees()
        self.update_vacation_cancel_menu()

    # -------------------- [관리자 모드] --------------------
    def open_admin_window(self):
        pwd = askstring("관리자 인증", "비밀번호를 입력하세요:", show="*")
        if pwd != "1212":
            messagebox.showerror("오류", "비밀번호가 틀렸습니다.")
            return
        admin_win = tk.Toplevel(self)
        admin_win.title("관리자 모드 - 기록 입력")
        admin_win.geometry("400x350")
        admin_win.resizable(False, False)
        frame = ttk.Frame(admin_win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # 직원 선택
        ttk.Label(frame, text="직원 선택:").pack(pady=5)
        conn = get_db_connection()
        all_employees = conn.execute("SELECT * FROM employees").fetchall()
        conn.close()
        employee_names = [emp['name'] for emp in all_employees]
        admin_employee_var = tk.StringVar()
        emp_combo = ttk.Combobox(frame, textvariable=admin_employee_var, values=employee_names, state="readonly")
        emp_combo.pack(fill=tk.X, padx=10)

        # 날짜 선택
        ttk.Label(frame, text="날짜:").pack(pady=5)
        admin_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_frame = ttk.Frame(frame)
        date_frame.pack(fill=tk.X, padx=10)
        date_entry = ttk.Entry(date_frame, textvariable=admin_date_var, state="readonly")
        date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def choose_date():
            cal_win = tk.Toplevel(admin_win)
            cal_win.title("날짜 선택")
            cal_win.geometry("400x400")
            cal_frame = ttk.Frame(cal_win, padding=10)
            cal_frame.pack(fill=tk.BOTH, expand=True)

            from tkcalendar import Calendar
            cal = Calendar(cal_frame, selectmode="day", date_pattern="yyyy-mm-dd", firstweekday="sunday", locale="ko_KR")
            cal.pack(pady=5, fill=tk.BOTH, expand=True)
            try:
                cal.selection_set(datetime.strptime(admin_date_var.get(), "%Y-%m-%d"))
            except:
                pass

            def set_date():
                selected_date = cal.selection_get()
                admin_date_var.set(selected_date.strftime("%Y-%m-%d"))
                cal_win.destroy()

            ttk.Button(cal_frame, text="확인", command=set_date).pack(pady=10)

        ttk.Button(date_frame, text="날짜 선택", command=choose_date).pack(side=tk.RIGHT, padx=5)

        # 내려온 시간
        ttk.Label(frame, text="내려온 시간 (HH:MM):").pack(pady=5)
        admin_break_down_entry = ttk.Entry(frame)
        admin_break_down_entry.pack(fill=tk.X, padx=10)

        # 올라온 시간
        ttk.Label(frame, text="올라온 시간 (HH:MM):").pack(pady=5)
        admin_break_up_entry = ttk.Entry(frame)
        admin_break_up_entry.pack(fill=tk.X, padx=10)

        def save_admin_record():
            selected_employee_name = admin_employee_var.get().strip()
            if not selected_employee_name:
                messagebox.showwarning("선택 필요", "직원을 선택하세요.")
                return
            employee_id = None
            for emp in all_employees:
                if emp['name'] == selected_employee_name:
                    employee_id = emp['id']
                    break
            if employee_id is None:
                messagebox.showerror("오류", "직원을 찾을 수 없습니다.")
                return

            record_date = admin_date_var.get()
            break_down_val = admin_break_down_entry.get().strip()
            break_up_val = admin_break_up_entry.get().strip()

            conn = get_db_connection()
            row = conn.execute("SELECT * FROM break_records WHERE employee_id=? AND record_date=?",
                               (employee_id, record_date)).fetchone()
            if row is None:
                conn.execute("INSERT INTO break_records (employee_id, record_date, break_down, break_up) VALUES (?, ?, ?, ?)",
                             (employee_id, record_date, break_down_val, break_up_val))
            else:
                conn.execute("UPDATE break_records SET break_down=?, break_up=? WHERE employee_id=? AND record_date=?",
                             (break_down_val, break_up_val, employee_id, record_date))
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", "기록이 저장되었습니다.")
            admin_win.destroy()
            self.load_employees()

        ttk.Button(frame, text="기록 저장", command=save_admin_record).pack(pady=15)

if __name__ == '__main__':
    # 중복 실행 방지 (락 파일 방식)
    LOCK_FILE = 'D_mode.lock'
    try:
        lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
    except OSError as e:
        if e.errno == errno.EEXIST:
            messagebox.showerror("중복 실행", "이미 프로그램이 실행 중입니다.")
            sys.exit(1)
        else:
            raise
    def remove_lock():
        try:
            os.close(lock_fd)
            os.remove(LOCK_FILE)
        except Exception:
            pass
    atexit.register(remove_lock)
    init_db()
    app = EmployeeManagerApp()
    app.mainloop()
