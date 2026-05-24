class PCMProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.targetSampleRate = 24000;
    this.sourceSampleRate = sampleRate;
    this.ratio = this.sourceSampleRate / this.targetSampleRate;
    this.history = [];
  }

  process(inputs) {
    const input = inputs[0]?.[0];
    if (!input) return true;

    if (Math.abs(this.ratio - 1) < 0.01) {
      const int16 = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      this.port.postMessage(int16, [int16.buffer]);
      return true;
    }

    const combined = new Float32Array(this.history.length + input.length);
    combined.set(this.history, 0);
    combined.set(input, this.history.length);
    
    const targetLength = Math.floor(combined.length / this.ratio);
    const resampled = new Float32Array(targetLength);

    for (let i = 0; i < targetLength; i++) {
      const sourceIdx = i * this.ratio;
      const idx = Math.floor(sourceIdx);
      const frac = sourceIdx - idx;

      if (idx >= combined.length - 1) {
        resampled[i] = combined[combined.length - 1];
      } else {
        resampled[i] = combined[idx] * (1 - frac) + combined[idx + 1] * frac;
      }
    }

    const keepIdx = Math.floor(targetLength * this.ratio);
    this.history = Array.from(combined.slice(keepIdx));

    const int16 = new Int16Array(resampled.length);
    for (let i = 0; i < resampled.length; i++) {
      const s = Math.max(-1, Math.min(1, resampled[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    this.port.postMessage(int16, [int16.buffer]);

    return true;
  }
}
registerProcessor('pcm-processor', PCMProcessor);
