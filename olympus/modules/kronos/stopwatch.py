import time
from enum import Enum
from typing import Optional


class StopwatchState(Enum):
	"""Enumeration of possible stopwatch states"""
	IDLE = 0
	RUNNING = 1
	PAUSED = 2
	STOPPED = 3

class Stopwatch:
	"""
	High-performance stopwatch for precise timing and benchmarking
	"""
	
	__slots__ = ("_start_time", "_pause_time", "_total_paused", "_state", "_final_time")
	
	def __init__(self):
		"""
		Initialize the stopwatch in idle state
		"""
		self._start_time: Optional[float] = None
		self._pause_time: Optional[float] = None
		self._total_paused: float = 0.0
		self._state: StopwatchState = StopwatchState.IDLE
	
	def start(self) -> "Stopwatch":
		"""
		Start the stopwatch timing
		
		Returns:
			Self for method chaining
			
		Raises:
			RuntimeError: If stopwatch is already running
		"""
		if self.is_running:
			raise RuntimeError("Stopwatch is already running")
		
		self._start_time = time.perf_counter()
		self._pause_time = None
		self._total_paused = 0.0
		self._state = StopwatchState.RUNNING

		return self
	
	def pause(self) -> "Stopwatch":
		"""
		Pause the stopwatch timing
		
		Returns:
			Self for method chaining
			
		Raises:
			RuntimeError: If stopwatch is not running
		"""
		if not self.is_running:
			raise RuntimeError("Stopwatch is not running")
		
		self._pause_time = time.perf_counter()
		self._state = StopwatchState.PAUSED

		return self
	
	def resume(self) -> "Stopwatch":
		"""
		Resume the stopwatch timing after a pause
		
		Returns:
			Self for method chaining
			
		Raises:
			RuntimeError: If stopwatch is not paused
		"""
		if not self.is_paused:
			raise RuntimeError("Stopwatch is not paused")
		
		current_time = time.perf_counter()
		self._total_paused += current_time - self._pause_time
		self._pause_time = None
		self._state = StopwatchState.RUNNING

		return self
	
	def stop(self) -> "Stopwatch":
		"""
		Stop the stopwatch timing
		
		Returns:
			Self for method chaining
			
		Raises:
			RuntimeError: If stopwatch is not running or paused
		"""
		if not self.is_running and not self.is_paused:
			raise RuntimeError("Stopwatch is not running")
		
		current_time = time.perf_counter()
		self._state = StopwatchState.STOPPED
		
		if self._state == StopwatchState.PAUSED:
			self._final_time = self._pause_time - self._start_time - self._total_paused
		else:
			self._final_time = current_time - self._start_time - self._total_paused

		return self
	
	def check(self) -> float:
		"""
		Get the current elapsed time in seconds
		
		Returns:
			Elapsed time in seconds. If stopped, returns total time.
			If running, returns current elapsed time. If paused, returns
			time elapsed up to the pause point
			
		Raises:
			RuntimeError: If stopwatch has never been started
		"""
		if self._start_time is None:
			raise RuntimeError("Stopwatch has never been started")
		
		if self._state == StopwatchState.RUNNING:
			return time.perf_counter() - self._start_time - self._total_paused
		
		if self._state == StopwatchState.PAUSED:
			return self._pause_time - self._start_time - self._total_paused
		
		if self._state == StopwatchState.STOPPED:
			return self._final_time
		
		return 0.0 # StopwatchState.IDLE
	
	def reset(self) -> "Stopwatch":
		"""
		Reset the stopwatch to idle state
		
		Returns:
			Self for method chaining
		"""
		self._start_time = None
		self._pause_time = None
		self._total_paused = 0.0
		self._state = StopwatchState.IDLE

		return self
	
	@property
	def state(self) -> StopwatchState:
		"""Get the current state of the stopwatch"""
		return self._state
	
	@property
	def is_running(self) -> bool:
		"""Check if the stopwatch is currently running"""
		return self._state == StopwatchState.RUNNING
	
	@property
	def is_paused(self) -> bool:
		"""Check if the stopwatch is currently paused"""
		return self._state == StopwatchState.PAUSED
	
	@property
	def is_stopped(self) -> bool:
		"""Check if the stopwatch is stopped"""
		return self._state == StopwatchState.STOPPED
	
	def __str__(self) -> str:
		"""String representation of the stopwatch"""
		try:
			elapsed = self.check()
			return f"Stopwatch({self._state.value}): {elapsed:.6f}s"
		except RuntimeError:
			return f"Stopwatch({self._state.value}): not started"
	
	def __repr__(self) -> str:
		"""Detailed representation of the stopwatch"""
		return (f"Stopwatch(state={self._state.value}, start_time={self._start_time}, total_paused={self._total_paused})")