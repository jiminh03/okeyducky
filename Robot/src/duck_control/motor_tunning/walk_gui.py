#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from threading import Thread, Event

from scservo_sdk import *

# ============================================
# 설정
# ============================================
PORT = "/dev/ttyUSB0"
BAUD = 1000000
POS_PER_DEG = 4096 / 360.0

MOTOR_IDS = [10,11,12,13,14, 20,21,22,23,24]

STEP_DIR = os.path.expanduser("~/motortest/steps")

# 폴더 없으면 생성
os.makedirs(STEP_DIR, exist_ok=True)

INIT_FILE = "init_pose.json"
LAST_FILE = "last_pose.json"

DEFAULT_INIT_POSE = {
    10:1975, 11:1867, 12:2634, 13:1193, 14:2404,
    20:2122, 21:2211, 22:1438, 23:2910, 24:1900,
}

# INIT_POSE 로드
if os.path.exists(INIT_FILE):
    try:
        with open(INIT_FILE, "r") as f:
            INIT_POSE = {int(k): v for k, v in json.load(f).items()}
        print("✓ INIT_POSE 로드됨")
    except:
        INIT_POSE = DEFAULT_INIT_POSE
else:
    INIT_POSE = DEFAULT_INIT_POSE


# ============================================
# 변환 함수
# ============================================
def pos_to_deg(mid, pos):
    return (pos - INIT_POSE[mid]) / POS_PER_DEG

def deg_to_pos(mid, deg):
    return int(INIT_POSE[mid] + deg * POS_PER_DEG)


# ============================================
# GUI CLASS
# ============================================
class MotorGUI:
    def __init__(self, root):
        self.root = root
        root.title("Duck Motor Full Control + JSON Sequence Player")

        # Servo init
        self.port = PortHandler(PORT)
        self.packet = sms_sts(self.port)

        if not self.port.openPort():
            messagebox.showerror("Error", "❌ 포트 오픈 실패")
            exit()
        if not self.port.setBaudRate(BAUD):
            messagebox.showerror("Error", "❌ 보레이트 설정 실패")
            exit()

        print("✓ 포트 연결됨")

        # UI components
        self.sliders = {}
        self.angle_labels = {}
        self.pos_labels = {}
        self.entry_boxes = {}

        # sequence list
        self.sequence_files = []
        self.loaded_pose = None

        # step interval
        self.step_interval = tk.DoubleVar(value=0.3)

        # loop control
        self.stop_event = Event()

        # build UI
        self.build_ui()
        self.update_angles()


    # ====================================================
    # UI 구성
    # ====================================================
    def build_ui(self):
        row = 0
        for mid in MOTOR_IDS:

            tk.Label(self.root, text=f"Motor {mid}", font=("Arial", 12, "bold"))\
                .grid(row=row, column=0, padx=5)

            # ----------------------------- #
            # Slider (절대 각도 제어)
            # ----------------------------- #
            slider = tk.Scale(
                self.root, from_=-90, to=90,
                orient=tk.HORIZONTAL, length=260, resolution=1,
                command=lambda val, m=mid: self.move_motor_absolute(m, float(val))
            )
            slider.grid(row=row, column=1)
            self.sliders[mid] = slider

            # angle label
            a = tk.Label(self.root, text="0.0°", width=10)
            a.grid(row=row, column=2)
            self.angle_labels[mid] = a

            # pos label
            p = tk.Label(self.root, text="pos: 0000", width=12)
            p.grid(row=row, column=3)
            self.pos_labels[mid] = p

            # Δ 입력
            entry = tk.Entry(self.root, width=6)
            entry.grid(row=row, column=4)
            entry.insert(0, "0")
            self.entry_boxes[mid] = entry

            tk.Button(
                self.root, text="Set Δ",
                command=lambda m=mid, e=entry: self.move_motor_relative(m, e)
            ).grid(row=row, column=5, padx=5)

            row += 1

        # =====================================================================
        # INIT / LAST pose control
        # =====================================================================
        tk.Button(self.root, text="Reset to INIT Pose", font=("Arial", 12),
                  command=self.reset_init_pose)\
            .grid(row=row, column=0, columnspan=3, pady=10)

        tk.Button(self.root, text="Return to LAST Pose", font=("Arial", 12),
                  command=self.return_last_pose)\
            .grid(row=row, column=3, columnspan=3, pady=10)

        row += 1

        # =====================================================================
        # Save pose
        # =====================================================================
        tk.Label(self.root, text="파일 이름:", font=("Arial", 11))\
            .grid(row=row, column=0)

        self.save_name_entry = tk.Entry(self.root, width=20)
        self.save_name_entry.grid(row=row, column=1)

        tk.Button(self.root, text="현재 포즈 저장",
                  command=self.save_pose)\
            .grid(row=row, column=2, padx=10)

        row += 1

        # =====================================================================
        # JSON 불러오기 UI
        # =====================================================================
        tk.Label(self.root, text="JSON 선택:", font=("Arial", 11))\
            .grid(row=row, column=0)

        self.json_combo = ttk.Combobox(
            self.root, width=25, values=self.scan_json_files()
        )
        self.json_combo.grid(row=row, column=1)

        tk.Button(self.root, text="불러오기",
                  command=self.load_json_pose)\
            .grid(row=row, column=2)

        tk.Button(self.root, text="적용",
                  command=self.apply_loaded_pose)\
            .grid(row=row, column=3)

        row += 1

        # =====================================================================
        # Sequence builder
        # =====================================================================
        tk.Label(self.root, text="Sequence:", font=("Arial", 11))\
            .grid(row=row, column=0)

        self.seq_list = tk.Listbox(self.root, width=30, height=8)
        self.seq_list.grid(row=row, column=1)

        tk.Button(self.root, text="Add →", command=self.add_to_sequence)\
            .grid(row=row, column=2, padx=4)

        row += 1

        # sequence controls
        tk.Button(self.root, text="Remove", width=10,
                  command=self.remove_selected)\
            .grid(row=row, column=1, sticky="w")

        tk.Button(self.root, text="Clear", width=10,
                  command=self.clear_sequence)\
            .grid(row=row, column=1)

        tk.Button(self.root, text="▲", width=5,
                  command=self.move_up)\
            .grid(row=row, column=2, sticky="w")

        tk.Button(self.root, text="▼", width=5,
                  command=self.move_down)\
            .grid(row=row, column=2, sticky="e")

        row += 1

        # =====================================================================
        # Interval + Play/Stop
        # =====================================================================
        tk.Label(self.root, text="Step Interval (sec):", font=("Arial", 11))\
            .grid(row=row, column=0)

        tk.Entry(self.root, textvariable=self.step_interval, width=5)\
            .grid(row=row, column=1, sticky="w")

        tk.Button(self.root, text="Play Sequence",
                  command=self.play_sequence)\
            .grid(row=row, column=2, pady=10)

        tk.Button(self.root, text="Play Loop",
                  command=self.play_loop)\
            .grid(row=row, column=3, pady=10)

        tk.Button(self.root, text="Stop",
                  command=self.stop_loop)\
            .grid(row=row, column=4, pady=10)

    # ====================================================
    # 절대각도 제어
    # ====================================================
    def move_motor_absolute(self, mid, deg):
        pos = deg_to_pos(mid, deg)
        self.packet.WritePosEx(mid, pos, 4000, 0)

    # ====================================================
    # 상대각도 제어 (Δ)
    # ====================================================
    def move_motor_relative(self, mid, entry):
        try:
            delta = float(entry.get())
        except:
            print("입력 오류")
            return

        pos, result, _ = self.packet.ReadPos(mid)
        if result != COMM_SUCCESS:
            return

        current_deg = pos_to_deg(mid, pos)
        new_deg = current_deg + delta
        target_pos = deg_to_pos(mid, new_deg)

        # UI 업데이트
        self.sliders[mid].set(new_deg)

        self.packet.WritePosEx(mid, target_pos, 4000, 0)

    # ====================================================
    # 실시간 각도 & pos 업데이트
    # ====================================================
    def update_angles(self):
        for mid in MOTOR_IDS:
            try:
                pos, result, err = self.packet.ReadPos(mid)
                if result == COMM_SUCCESS:
                    deg = pos_to_deg(mid, pos)
                    self.angle_labels[mid].config(text=f"{deg:.1f}°")
                    self.pos_labels[mid].config(text=f"pos: {pos}")
            except:
                pass

        self.root.after(50, self.update_angles)

    # ====================================================
    # INIT 포즈
    # ====================================================
    def reset_init_pose(self):
        for mid, pos in INIT_POSE.items():
            self.packet.WritePosEx(mid, pos, 2000, 0)

    # ====================================================
    # LAST 포즈 복귀
    # ====================================================
    def return_last_pose(self):
        if not os.path.exists(LAST_FILE):
            messagebox.showwarning("Warning", "마지막 pose 없음!")
            return

        with open(LAST_FILE, "r") as f:
            pose = {int(k): v for k, v in json.load(f).items()}

        for mid, pos in pose.items():
            self.packet.WritePosEx(mid, pos, 2000, 0)

    # ====================================================
    # pose 저장 (현재 모터 위치 → JSON)
    # ====================================================
    def save_pose(self):
        pose = {}
        for mid in MOTOR_IDS:
            pos, result, err = self.packet.ReadPos(mid)
            if result == COMM_SUCCESS:
                pose[mid] = pos
            else:
                pose[mid] = INIT_POSE[mid]

        filename = self.save_name_entry.get().strip()

        if filename == "":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pose_{timestamp}.json"

        if not filename.endswith(".json"):
            filename += ".json"

        file_path = os.path.join(STEP_DIR, filename)

        with open(file_path, "w") as f:
            json.dump(pose, f, indent=4)

        # last pose 업데이트
        with open(LAST_FILE, "w") as f:
            json.dump(pose, f, indent=4)

        messagebox.showinfo("저장 완료", f"{file_path} 저장됨!")

        # 콤보박스 갱신
        self.json_combo["values"] = self.scan_json_files()

    # ====================================================
    # steps/ 폴더 내 json 파일 검색
    # ====================================================
    def scan_json_files(self):
        return sorted([f for f in os.listdir(STEP_DIR) if f.endswith(".json")])

    # ====================================================
    # JSON 불러오기 (GUI 선택)
    # ====================================================
    def load_json_pose(self):
        name = self.json_combo.get()
        if name == "":
            messagebox.showwarning("Warning", "JSON 파일을 선택하세요!")
            return

        path = os.path.join(STEP_DIR, name)

        with open(path, "r") as f:
            self.loaded_pose = {int(k): v for k, v in json.load(f).items()}

        messagebox.showinfo("로드 완료", f"{name} 로드됨!")

    # ====================================================
    # 로드된 JSON pose 적용
    # ====================================================
    def apply_loaded_pose(self):
        if not hasattr(self, "loaded_pose") or self.loaded_pose is None:
            messagebox.showwarning("Warning", "로드된 pose 없음!")
            return

        for mid, pos in self.loaded_pose.items():
            self.packet.WritePosEx(mid, pos, 2000, 0)

    # ====================================================
    # Sequence 관리 기능
    # ====================================================
    def add_to_sequence(self):
        name = self.json_combo.get()
        if name == "":
            return
        self.seq_list.insert(tk.END, name)

    def remove_selected(self):
        sel = self.seq_list.curselection()
        if sel:
            self.seq_list.delete(sel[0])

    def clear_sequence(self):
        self.seq_list.delete(0, tk.END)

    def move_up(self):
        sel = self.seq_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == 0:
            return
        item = self.seq_list.get(idx)
        self.seq_list.delete(idx)
        self.seq_list.insert(idx-1, item)
        self.seq_list.selection_set(idx-1)

    def move_down(self):
        sel = self.seq_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == self.seq_list.size()-1:
            return
        item = self.seq_list.get(idx)
        self.seq_list.delete(idx)
        self.seq_list.insert(idx+1, item)
        self.seq_list.selection_set(idx+1)

    # ====================================================
    # Sequence 실행
    # ====================================================
    def play_sequence(self):
        seq = list(self.seq_list.get(0, tk.END))
        if not seq:
            messagebox.showwarning("Warning", "Sequence 비어 있음!")
            return

        interval = self.step_interval.get()

        def run():
            self.disable_buttons()
            for file in seq:
                path = os.path.join(STEP_DIR, file)
                with open(path, "r") as f:
                    pose = {int(k): v for k, v in json.load(f).items()}
                for mid, pos in pose.items():
                    self.packet.WritePosEx(mid, pos, 2000, 0)
                time.sleep(interval)
            self.enable_buttons()
            messagebox.showinfo("완료", "Sequence 실행 완료!")

        Thread(target=run, daemon=True).start()

    # ====================================================
    # Loop 실행
    # ====================================================
    def play_loop(self):
        seq = list(self.seq_list.get(0, tk.END))
        if not seq:
            messagebox.showwarning("Warning", "Sequence 비어 있음!")
            return

        self.stop_event.clear()
        interval = self.step_interval.get()

        def run():
            self.disable_buttons()
            while not self.stop_event.is_set():
                for file in seq:
                    if self.stop_event.is_set():
                        break
                    path = os.path.join(STEP_DIR, file)
                    with open(path, "r") as f:
                        pose = {int(k): v for k, v in json.load(f).items()}
                    for mid, pos in pose.items():
                        self.packet.WritePosEx(mid, pos, 2000, 0)
                    time.sleep(interval)
            self.enable_buttons()

        Thread(target=run, daemon=True).start()

    # ====================================================
    # Loop 중단
    # ====================================================
    def stop_loop(self):
        self.stop_event.set()

    # ====================================================
    # 버튼 활성/비활성 (슬라이더는 유지)
    # ====================================================
    def disable_buttons(self):
        for child in self.root.winfo_children():
            if isinstance(child, tk.Button) and child['text'] not in ["Stop"]:
                child.config(state="disabled")

    def enable_buttons(self):
        for child in self.root.winfo_children():
            if isinstance(child, tk.Button):
                child.config(state="normal")

# ====================================================
# 실행
# ====================================================
if __name__ == "__main__":
    root = tk.Tk()
    gui = MotorGUI(root)
    root.mainloop()

