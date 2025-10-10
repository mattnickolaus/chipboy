package main

import (
	"math"
	"math/rand"
	"time"

	"github.com/gopxl/beep"
	"github.com/gopxl/beep/speaker"
)

type SineWaveStreamer struct {
	pos      int
	freq     float64
	amp      float64
	format   beep.Format
	duration time.Duration
}

func NewSineWaveStreamer(freq, amp float64, format beep.Format, duration time.Duration) *SineWaveStreamer {
	return &SineWaveStreamer{
		freq:     freq,
		amp:      amp,
		format:   format,
		duration: duration,
	}
}

func (s *SineWaveStreamer) Stream(samples [][2]float64) (n int, ok bool) {
	numSamples := int(s.duration.Seconds() * float64(s.format.SampleRate))
	if s.pos >= numSamples {
		return 0, false // End of sound
	}

	for i := range samples {
		if s.pos >= numSamples {
			break
		}
		t := float64(s.pos) / float64(s.format.SampleRate)
		val := s.amp * math.Sin(2*math.Pi*s.freq*t)
		samples[i][0] = val // Left channel
		samples[i][1] = val // Right channel
		s.pos++
		n++
	}
	return n, true
}

func (s *SineWaveStreamer) Err() error {
	return nil
}

func (s *SineWaveStreamer) Len() int {
	return int(s.duration.Seconds() * float64(s.format.SampleRate))
}

func (s *SineWaveStreamer) Position() int {
	return s.pos
}

// Implementing a Noise stream using the beep.StreamerFunc helper type (demoed in the docs)
/*
Notes:
Likely won't use this as I will want a datastructure for each note type to set parameters for each note
*/
func Noise() beep.Streamer {
	return beep.StreamerFunc(func(samples [][2]float64) (n int, ok bool) {
		for i, _ := range samples {
			samples[i][0] = 0.1 * (rand.Float64()*2 - 1)
			samples[i][1] = 0.1 * (rand.Float64()*2 - 1)
		}
		return len(samples), true
	})
}

type Queue struct {
	streamers []beep.Streamer
}

func (q *Queue) Add(streamers ...beep.Streamer) {
	q.streamers = append(q.streamers, streamers...)
}

func (q *Queue) Stream(samples [][2]float64) (n int, ok bool) {
	// We use the filled variable to track how many samples we've
	// successfully filled already. We loop until all samples are filled.
	filled := 0
	for filled < len(samples) {
		// There are no streamers in the queue, so we stream silence.
		if len(q.streamers) == 0 {
			for i := range samples[filled:] {
				samples[i][0] = 0
				samples[i][1] = 0
			}
			break
		}

		// We stream from the first streamer in the queue.
		n, ok := q.streamers[0].Stream(samples[filled:])
		// If it's drained, we pop it from the queue, thus continuing with
		// the next streamer.
		if !ok {
			q.streamers = q.streamers[1:]
		}
		// We update the number of filled samples.
		filled += n
	}
	return len(samples), true
}

func (q *Queue) Err() error {
	return nil
}

func main() {
	sampleRate := beep.SampleRate(44100)
	speaker.Init(sampleRate, sampleRate.N(time.Second/10))

	freq := 440.0 // A4 note
	amplitude := 0.5
	duration := 1 * time.Second

	sineStreamer := NewSineWaveStreamer(freq, amplitude, beep.Format{SampleRate: sampleRate}, duration)

	var queue Queue
	queue.Add(NewSineWaveStreamer(261.63, amplitude, beep.Format{SampleRate: sampleRate}, duration)) // C4 note
	queue.Add(sineStreamer)
	queue.Add(Noise(), Noise())

	done := make(chan bool)
	speaker.Play(beep.Seq(beep.Take(sampleRate.N(2500*time.Millisecond), &queue), beep.Callback(func() {
		done <- true
	})))
	<-done
}
