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
		duration: duration}
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
	duration  time.Duration
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

func sweep(streamer beep.Streamer, duration time.Duration) beep.Streamer {
	resampler := beep.ResampleRatio(4, 1, streamer)
	go func() {
		start := time.Now()
		for {
			elapsed := time.Since(start)
			if elapsed >= duration {
				break
			}
			ratio := 1.0 + (elapsed.Seconds()/duration.Seconds())*4.0 // linear sweep from 1.0 to 2.0
			resampler.SetRatio(ratio)
			time.Sleep(10 * time.Millisecond)
		}
	}()
	return resampler
}

func exponentialSweep(streamer beep.Streamer, duration time.Duration, endRatio float64) beep.Streamer {
	resampler := beep.ResampleRatio(4, 1, streamer)
	go func() {
		start := time.Now()
		for {
			elapsed := time.Since(start)
			if elapsed >= duration {
				break
			}
			progress := elapsed.Seconds() / duration.Seconds()
			ratio := math.Pow(endRatio, progress)
			resampler.SetRatio(ratio)
			time.Sleep(10 * time.Millisecond)
		}
	}()
	return resampler
}

func logarithmicSweep(streamer beep.Streamer, duration time.Duration, endRatio float64) beep.Streamer {
	resampler := beep.ResampleRatio(4, 1, streamer)
	go func() {
		start := time.Now()
		for {
			elapsed := time.Since(start)
			if elapsed >= duration {
				break
			}
			progress := elapsed.Seconds() / duration.Seconds()
			ratio := 1.0 + (endRatio-1.0)*math.Log(1+progress*(math.E-1))
			resampler.SetRatio(ratio)
			time.Sleep(10 * time.Millisecond)
		}
	}()
	return resampler
}

func main() {
	sampleRate := beep.SampleRate(44100)
	speaker.Init(sampleRate, sampleRate.N(time.Second/10))

	sawA4 := Note{
		Frequency:     987.767,
		DurationBeats: 0.25,
		Volume:        1,
		Waveform:      Square,
	}

	squareE6 := Note{
		Frequency:     1318.51,
		DurationBeats: 0.5,
		Volume:        1,
		Waveform:      Square,
	}

	// sawC4 := Note{
	// Frequency:     261.63,
	// DurationBeats: 0.25,
	// Volume:        1,
	// Waveform:      Square,
	// }
	//
	rest := Note{
		Frequency:     440.0,
		DurationBeats: 0.25,
		Volume:        1,
		Waveform:      Rest,
	}
	//
	// halfRest := Note{
	// Frequency:     440.0,
	// DurationBeats: 2,
	// Volume:        1,
	// Waveform:      Rest,
	// }
	//
	// noise := Note{
	// DurationBeats: 0.25,
	// Waveform:      Noise,
	// }

	var totalDuration time.Duration

	var queue Queue
	sawA4Stream, sawA4Duration := sawA4.ToStreamer(120.0, sampleRate)
	totalDuration += sawA4Duration
	queue.Add(sawA4Stream)

	squareE6Stream, squareE6Duration := squareE6.ToStreamer(120.0, sampleRate)
	totalDuration += squareE6Duration
	queue.Add(squareE6Stream)

	restStream, restDuration := rest.ToStreamer(120, sampleRate)
	totalDuration += restDuration
	queue.Add(restStream)

	// sawA4Stream, sawA4Duration = sawA4.ToStreamer(120.0, sampleRate)
	// queue.Add(exponentialSweep(sawA4Stream, sawA4Duration, 1.0))
	// totalDuration += sawA4Duration

	// restStream, restDuration = rest.ToStreamer(120, sampleRate)
	// totalDuration += restDuration
	// queue.Add(restStream)

	// sawA4Stream, sawA4Duration = sawA4.ToStreamer(120.0, sampleRate)
	// queue.Add(logarithmicSweep(sawA4Stream, sawA4Duration, 1.0))
	// totalDuration += sawA4Duration

	// restStream, restDuration := rest.ToStreamer(120, sampleRate)
	// totalDuration += restDuration
	// queue.Add(restStream)
	//
	// sawA4Stream, sawA4Duration = sawA4.ToStreamer(120.0, sampleRate)
	// totalDuration += sawA4Duration
	// queue.Add(sawA4Stream)
	//
	// sawC4Stream, sawC4Duration := sawC4.ToStreamer(120.0, sampleRate)
	// totalDuration += sawC4Duration
	// queue.Add(sawC4Stream)
	//
	// restStream, restDuration = rest.ToStreamer(120, sampleRate)
	// totalDuration += restDuration
	// queue.Add(restStream)
	//
	// sawC4Stream, sawC4Duration = sawC4.ToStreamer(120.0, sampleRate)
	// totalDuration += sawC4Duration
	// queue.Add(sawC4Stream)
	//
	// restStream, restDuration = rest.ToStreamer(120, sampleRate)
	// totalDuration += restDuration
	// queue.Add(restStream)
	//
	// noiseStream, noiseDuration := noise.ToStreamer(120, sampleRate)
	// totalDuration += noiseDuration
	// queue.Add(noiseStream)
	//
	// halfRestStream, halfRestDuration := halfRest.ToStreamer(120, sampleRate)
	// totalDuration += halfRestDuration
	// queue.Add(halfRestStream)
	//
	// sawC4Stream, sawC4Duration = sawC4.ToStreamer(120.0, sampleRate)
	// totalDuration += sawC4Duration
	// queue.Add(sawC4Stream)
	//
	// sawA4Stream, sawA4Duration = sawA4.ToStreamer(120.0, sampleRate)
	// totalDuration += sawA4Duration
	// queue.Add(sawA4Stream)
	//
	// restStream, restDuration = rest.ToStreamer(120, sampleRate)
	// totalDuration += restDuration
	// queue.Add(restStream)

	done := make(chan bool)
	speaker.Play(beep.Seq(beep.Take(sampleRate.N(totalDuration), &queue), beep.Callback(func() {
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
