package main

import (
	"math/rand"
	"time"

	"github.com/gopxl/beep"
	"github.com/gopxl/beep/generators"
)

type WaveformType string

const (
	Sine     WaveformType = "sine"
	Square   WaveformType = "square"
	Sawtooth WaveformType = "sawtooth"
	Noise    WaveformType = "noise"
	Rest     WaveformType = "rest"
)

type Note struct {
	Frequency     float64
	DurationBeats float64
	Volume        float64
	Waveform      WaveformType
}

func (n *Note) ToStreamer(bpm float64, sampleRate beep.SampleRate) (beep.Streamer, time.Duration) {
	duration := time.Duration((n.DurationBeats * 60 / bpm) * float64(time.Second))
	numSamples := sampleRate.N(duration)

	var streamer beep.Streamer

	switch n.Waveform {
	case Sine:
		streamer, _ = generators.SineTone(sampleRate, n.Frequency)
	case Square:
		streamer, _ = generators.SquareTone(sampleRate, n.Frequency)
	case Sawtooth:
		streamer, _ = generators.SawtoothTone(sampleRate, n.Frequency)
	case Noise:
		streamer = generateNoise()
	case Rest:
		streamer = generators.Silence(-1)
	default:
		streamer, _ = generators.SineTone(sampleRate, n.Frequency)
	}

	return beep.Take(numSamples, streamer), duration
}

// Implementing a Noise stream using the beep.StreamerFunc helper type (demoed in the docs)

/*
Notes:
Likely won't use this as I will want a datastructure for each note type to set parameters for each note
*/
func generateNoise() beep.Streamer {
	return beep.StreamerFunc(func(samples [][2]float64) (n int, ok bool) {
		for i, _ := range samples {
			samples[i][0] = 0.5 * (rand.Float64()*2 - 1)
			samples[i][1] = 0.5 * (rand.Float64()*2 - 1)
		}
		return len(samples), true
	})
}
