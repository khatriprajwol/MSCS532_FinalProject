"""
data_structures.py

Two from-scratch data structures used to demonstrate the "data locality
optimization" technique documented in Azad et al. (2023), "An Empirical
Study of High Performance Computing (HPC) Performance Bugs" (MSR 2023).

The comparison is deliberately narrow: both structures support only the
three operations a traversal-vs-access benchmark actually needs -
appending a value, reading a value by position, and summing every value
in order - so the only real difference between them is how the values
sit in memory.

  LinkedList      Each value lives in its own heap object, linked to the
                   next one by a pointer. Memory layout is whatever the
                   allocator happens to hand back; nothing enforces
                   adjacency between logically consecutive elements.

  ContiguousArray  Every value lives in the same block of memory, one
                   slot after another, the way a C array or std::vector
                   is laid out. The block is grown by doubling rather
                   than by allocating one slot at a time.

Public class and method names (LinkedList, ContiguousArray, append, get,
traverse_sum) are kept stable because the accompanying project report
refers to them directly. Everything below the public surface - internal
field names, docstring wording, error messages, and code layout - was
written independently for this project rather than following a single
canonical textbook implementation.
"""

from __future__ import annotations

import ctypes


class Node:
    """One link in the chain: a payload value and a reference forward."""

    __slots__ = ("value", "next")

    def __init__(self, value: int) -> None:
        self.value = value
        self.next = None


class LinkedList:
    """
    Singly linked chain of independently allocated Node objects.

    Nothing about this structure guarantees that node N and node N+1
    occupy nearby addresses - each append() call asks the allocator for
    a fresh block, and the allocator is free to place it anywhere. That
    is the property under test: does scattering elements across memory
    cost anything measurable when the structure is read back?

    This class stands in for the forward_list / linked-list pattern that
    Section III-A4 of the empirical study names as a recurring source of
    inefficient-data-structure bugs.
    """

    def __init__(self) -> None:
        self._first = None
        self._last = None
        self._count = 0

    def append(self, value: int) -> None:
        """Add value to the end of the chain."""
        new_node = Node(value)
        if self._first is None:
            self._first = new_node
            self._last = new_node
        else:
            self._last.next = new_node
            self._last = new_node
        self._count += 1

    def get(self, position: int) -> int:
        """
        Return the value at `position`, counting from the front.

        There is no shortcut here: reaching element k means visiting
        elements 0 through k-1 first, so this call costs O(position).
        """
        self._check_bounds(position)
        cursor = self._first
        for _ in range(position):
            cursor = cursor.next
        return cursor.value

    def traverse_sum(self) -> int:
        """Walk the chain once, front to back, and add up every value."""
        running_total = 0
        cursor = self._first
        while cursor is not None:
            running_total += cursor.value
            cursor = cursor.next
        return running_total

    def _check_bounds(self, position: int) -> None:
        if not (0 <= position < self._count):
            raise IndexError(
                f"position {position} is outside the valid range "
                f"[0, {self._count})"
            )

    def __len__(self) -> int:
        return self._count


class ContiguousArray:
    """
    A single, densely packed block of fixed-width integers.

    Storage is a raw ctypes array rather than Python's built-in list or
    array module, so the growth policy and slot layout are both fully
    visible here instead of hidden behind a C-implemented container.
    Every element occupies exactly ctypes.sizeof(SLOT_TYPE) bytes,
    immediately after the previous one, which is the layout property
    Section IV-A1a of the empirical study identifies as the fix for the
    forward_list / std::list inefficiency pattern (replace the linked
    container with vector or array).

    Growth is geometric (capacity doubles when full), matching the
    amortized-O(1) append behavior of std::vector and CPython's own
    list, but implemented by hand with ctypes.memmove rather than
    delegated to either.
    """

    SLOT_TYPE = ctypes.c_long  # platform integer, 8 bytes on most 64-bit systems

    def __init__(self, starting_capacity: int = 8) -> None:
        self._capacity = max(1, starting_capacity)
        self._count = 0
        self._slots = self._make_block(self._capacity)

    def append(self, value: int) -> None:
        """Write value into the next free slot, growing the block first if full."""
        if self._count == self._capacity:
            self._expand()
        self._slots[self._count] = value
        self._count += 1

    def get(self, position: int) -> int:
        """
        Return the value at `position` in O(1) - a direct offset into
        the block, no pointer to follow.
        """
        self._check_bounds(position)
        return self._slots[position]

    def traverse_sum(self) -> int:
        """Walk the block once, front to back, and add up every value."""
        running_total = 0
        slots = self._slots
        for i in range(self._count):
            running_total += slots[i]
        return running_total

    def _expand(self) -> None:
        """Double capacity and copy the live bytes into the new block."""
        bigger_capacity = self._capacity * 2
        bigger_block = self._make_block(bigger_capacity)
        live_bytes = ctypes.sizeof(self.SLOT_TYPE) * self._count
        ctypes.memmove(bigger_block, self._slots, live_bytes)
        self._slots = bigger_block
        self._capacity = bigger_capacity

    def _make_block(self, capacity: int):
        return (self.SLOT_TYPE * capacity)()

    def _check_bounds(self, position: int) -> None:
        if not (0 <= position < self._count):
            raise IndexError(
                f"position {position} is outside the valid range "
                f"[0, {self._count})"
            )

    def __len__(self) -> int:
        return self._count


def build_linked_list(size: int) -> LinkedList:
    """Construct a LinkedList holding the integers 0..size-1 in order."""
    chain = LinkedList()
    for value in range(size):
        chain.append(value)
    return chain


def build_contiguous_array(size: int) -> ContiguousArray:
    """Construct a ContiguousArray holding the integers 0..size-1 in order."""
    block = ContiguousArray(starting_capacity=8)
    for value in range(size):
        block.append(value)
    return block
