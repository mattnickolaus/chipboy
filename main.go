package main

import (
	"math"
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

	sawA4 := Note{
		Frequency:     440.0,
		DurationBeats: 0.25,
		Volume:        1,
		Waveform:      Square,
	}

	sawC4 := Note{
		Frequency:     261.63,
		DurationBeats: 0.25,
		Volume:        1,
		Waveform:      Square,
	}

	rest := Note{
		Frequency:     440.0,
		DurationBeats: 0.25,
		Volume:        1,
		Waveform:      Rest,
	}

	halfRest := Note{
		Frequency:     440.0,
		DurationBeats: 2,
		Volume:        1,
		Waveform:      Rest,
	}

	noise := Note{
		DurationBeats: 0.25,
		Waveform:      Noise,
	}

	var queue Queue
	queue.Add(sawA4.ToStreamer(120.0, sampleRate))
	queue.Add(rest.ToStreamer(120, sampleRate))
	queue.Add(sawA4.ToStreamer(120.0, sampleRate))
	queue.Add(sawC4.ToStreamer(120.0, sampleRate))
	queue.Add(rest.ToStreamer(120, sampleRate))
	queue.Add(sawC4.ToStreamer(120.0, sampleRate))
	queue.Add(rest.ToStreamer(120, sampleRate))
	queue.Add(noise.ToStreamer(120, sampleRate))
	queue.Add(halfRest.ToStreamer(120, sampleRate))
	queue.Add(sawC4.ToStreamer(120.0, sampleRate))
	queue.Add(rest.ToStreamer(120, sampleRate))
	queue.Add(sawA4.ToStreamer(120.0, sampleRate))

	done := make(chan bool)
	speaker.Play(beep.Seq(beep.Take(sampleRate.N(30000*time.Millisecond), &queue), beep.Callback(func() {
		done <- true
	})))
	<-done

	/*
		speaker.Play(beep.Seq(beep.Take(sampleRate.N(4000*time.Millisecond), &queue), beep.Callback(func() {
			done <- true
		})))
		<-done
	*/
}
