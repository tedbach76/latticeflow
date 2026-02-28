LatticeFlow: Architectural Design Notes

Project Scope: A high-performance, generative framework for Reversible Cellular Automata (CA) and Lattice Gas Automata (LGA).
Architect: Ted Bach (Ph.D., Boston University, 2007)
Co-Programmer: Gemini Pro (LLM)
Date: February 28, 2026

1. Architectural Philosophy: Decoupling and Reversibility

LatticeFlow is built upon the fundamental principle of strictly separating the two physical phases of a discrete system:

Transport (The Shift): The linear movement of data (particles/signals) through space. This is a non-local operation representing momentum and convection.

Interaction (The Rule): The local exchange of state at a single site (collisions). This is a strictly local operation where mass and energy are conserved.

Parsimonious Expression of Physics

A core tenet of the architecture is Parsimonious Expression. By isolating the local collision logic from the global data movement, we achieve a minimal description of the physical system. The complexity of the software should be proportional to the complexity of the physical rules (the "Generative Seed"), not the underlying memory management or hardware orchestration.

The "Bennett Echo" Requirement

To ensure bit-perfect reversibility, the architecture must support the Phase-Sync Bridge. Reversing the arrow of time is not merely inverting velocity vectors; it requires an additional standalone "Interaction" firing during the pivot to un-collide particles before the first backward shift.

2. Technical Lineage & Precepts

LatticeFlow represents the third generation of this software architecture, inheriting key precepts from the SIMP/STEP environment.

Generation

Technology

Data Movement

Logic Execution

CAM-8 (1990s)

Hardware

Physical Wires

SRAM Lookup Tables (LUTs)

SIMP/STEP (2000s)

Python DSL to C

Virtual Interrupts

Compiled C-macros

LatticeFlow (2020s)

JAX / XLA

Vectorized Tensor Rolls

Fused Bitwise Kernels

The SIMP/STEP Precepts

Space as an Array of Processors: Logic is defined from the perspective of a single site, assuming a homogeneous space.

Virtual Interrupts: Using logical "breaks" to handle non-local events (boundaries, probes) without polluting the main physical rule.

High-Level Specification: Defining physics in a human-readable Domain Specific Language (DSL) that is later lowered to high-performance primitives.

3. The Generative Physics Layer

A core innovation of this project is the use of Generative Physics—the collaboration between a human architect and an LLM to "compile" physical laws into code.

Workflow: The human provides a high-level physical description (e.g., "HPP collisions with mass conservation").

Synthesis: The LLM translates this into optimized, bit-packed JAX kernels.

Provenance: This validates the Entropy of Ideas thesis, where the complexity of the software is derived from the "Generative Seed" rather than manual line-by-line coding.

4. The Notebook as the Laboratory

The architecture adopts the Notebook (Google Colab / Jupyter) format not just for documentation, but as the primary Integrated Development Environment (IDE).

Unified Interface: The notebook seamlessly integrates the narrative (the physics description), the generative engine (the code synthesis), and the real-time visualization (rendered lattice flows).

Reproducibility: A notebook provides a self-contained environment that encapsulates the entire provenance of an experiment, from the architectural intent to the bit-perfect result.

5. Performance Metrics (Benchmarks)

Benchmarked on an Intel(R) Xeon(R) Broadwell (2 Cores, 55MB L3 Cache) within a Google Colab environment:

Peak Performance (HPP Bitwise Kernel): 1.47 GSPS (Giga-Sites Per Second).

Interactive Performance (With UI/Render): ~25.8 MSPS (Mega-Sites Per Second).

Real-world Echo Time: A 2,000-step "there and back" journey (1,000 steps forward + 1,000 steps reversed) resolves in ~20 seconds of clock time.

Acceleration Potential: The JAX-native implementation allows for immediate dispatch to GPU/TPU hardware for massive parallel scaling beyond SIMD limits.

6. Future Directions: The Common LatticeFlow Library

The long-term goal is to establish a formal Common LatticeFlow Library that serves as a standard for digital physics research.

Unified API: Developing a common interface that allows researchers to plug in new "Interaction Rules" while inheriting optimized "Transport" and "Rendering" pipelines.

Legacy Porting: Porting the historical codebase at threekings/simpstep using Gemini CLI as a primary autonomous translation agent.

Complex Topologies: Implementing multi-site partitioning logic, specifically the Polymer Rule (polymer.py), using 'pinwheel' neighborhoods.

GPU Dispatch: Benchmarking the common library on high-density GPU clusters to achieve hundreds of GSPS.

7. Key References

Dissertation: Bach, E. A. (2007). Methodology and Implementation of a Software Architecture for Cellular and Lattice-Gas Automata. Ph.D., Boston University.

Literature: Toffoli & Margolus (1987), Cellular Automata Machines; Bennett (1973), Logical Reversibility of Computation.

Experiment: Live Interactive HPP Echo (Google Colab)