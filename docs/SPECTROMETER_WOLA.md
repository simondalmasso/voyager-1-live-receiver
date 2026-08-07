# Deep-space spectrometer

The listener preserves `SIMPLE_FFT` as baseline and adds a four-tap WOLA/polyphase path. The prototype is a deterministic windowed-sinc FIR decomposed into four phases before the FFT. Tests compare an inter-bin tone against the simple Hann FFT and require materially lower far sidelobes.

Configuration declares FFT size, taps, integration method and window count. Products report effective bin width, integration duration and units. Incoherent/rolling/accumulated paths average linear power; coherent integration is only used on aligned complex windows and is labeled explicitly. Output is relative `dBFS_RELATIVE`; no arbitrary SDR value becomes dBm.
