<template>
    <div class="w-[800px] relative">
        <div ref="plotContainer"></div>
        <h1 class="text-3xl font-bold mb-6 text-center absolute top-8 left-16">EEG Spectrogram</h1>
        <div class="flex items-center gap-4">
            <button class="ml-8 bg-[#2B2D31] hover:bg-[#1B1D21] transition-colors p-2" @click="saveSpectrogram">💾 Save
                Spectrogram</button>
            <button class="ml-4 bg-[#2B2D31] hover:bg-[#1B1D21] transition-colors p-2" @click="saveCNNInput">🖼️ Save
                CNN Input Frame</button>
        </div>
        <canvas ref="spectroImageCan" class="hidden"></canvas>
    </div>
</template>

<script setup>
import * as tf from '@tensorflow/tfjs';
import { loadGraphModel } from '@tensorflow/tfjs-converter';
import { ref, watch, onMounted } from 'vue';
import FFT from 'fft.js';
import Plotly from 'plotly.js-dist';
import seedRandom from 'seedrandom';
let rng = seedRandom('0');

const { eegData, frameNumber } = defineProps({
    eegData: Array,
    frameNumber: Number
})

const predictions = defineModel({
    default: [0, 0, 0]
})

const spectroImageCan = ref(null);
const plotContainer = ref(null);

const oldNumWindows = ref(0);
const MODEL_URL = './tf_model/model.json';
const sampleRate = 512; // Sampling rate in Hz
const windowSize = 512; // Window size for STFT (in samples)
const stepSize = 256; // Step size for moving window (in samples)
const freqResolution = sampleRate / windowSize; // Frequency resolution in Hz
let model = null;
let spectrogramData = []; // 2D array to store spectrogram

function saveSpectrogram() {
    spectroImageCan.value.width = spectrogramData.length;
    spectroImageCan.value.height = spectrogramData[0].length;
    const ctx = spectroImageCan.value.getContext('2d');
    ctx.clearRect(0, 0, spectroImageCan.value.width, spectroImageCan.value.height);
    for (let i = 0; i < spectrogramData.length; i++) {
        for (let j = 0; j < spectrogramData[i].length; j++) {
            const transformedValue = (Math.max(-25, Math.min(spectrogramData[i][j], 10))+25)/35*255;
            ctx.fillStyle = `rgb(${transformedValue}, ${transformedValue}, ${transformedValue})`;
            ctx.fillRect(i, spectrogramData[0].length-j-1, 1, 1);
        }
    }
    spectroImageCan.value.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'spectrogram.png';
        a.click();
    });
}

function saveCNNInput() {
    const numWindows = Math.min(Math.max(1, (frameNumber * 2) / windowSize), spectrogramData.length);
    savePartialSpectrogram(1, Math.floor(numWindows - 30), Math.floor(numWindows));
}

function mergeRanges(range1, range2) {
    if (range1[0] < range2[0]) {
        if (range1[1] < range2[0]) {
            return [range1, range2];
        }
        if (range1[1] < range2[1]) {
            return [[range1[0], range2[1]]];
        }
        return [[range1[0], range1[1]]];
    }
    return mergeRanges(range2, range1);
}

function savePartialSpectrogram(amount, sampleStart, sampleEnd) {
    rng = seedRandom("" + spectrogramData[0][0] * spectrogramData[0][1]);
    const tickleStart = Math.floor(rng() * 90 + 40);
    const tickleEnd = tickleStart + Math.floor(rng() * 30 + 20);
    rng = seedRandom("" + spectrogramData[0][0] * spectrogramData[0][1]);
    const anesthesiaStart = Math.floor(rng() * 30 + 15);
    const anesthesiaEnd = spectrogramData.length - Math.floor(rng() * 30 + 15);
    const sampleWidth = 30;
    for (let sampleNum = 0; sampleNum < amount; sampleNum++) {
        sampleStart = sampleStart ?? Math.floor(Math.random() * (spectrogramData.length - sampleWidth));
        sampleEnd = sampleEnd ?? sampleStart + sampleWidth;
        console.log(sampleStart, sampleEnd);
        const containsTickle = mergeRanges([sampleStart, sampleEnd], [tickleStart, tickleEnd]).length === 1;
        const containsAnesthesia = mergeRanges([sampleStart, sampleEnd], [anesthesiaStart, anesthesiaEnd]).length === 1;
        // const containsTickle = false;
        // const containsAnesthesia = false;
        spectroImageCan.value.width = sampleWidth;
        spectroImageCan.value.height = spectrogramData[0].length;
        const ctx = spectroImageCan.value.getContext('2d');
        ctx.clearRect(0, 0, spectroImageCan.value.width, spectroImageCan.value.height);
        for (let i = sampleStart; i < sampleEnd; i++) {
            for (let j = 0; j < spectrogramData[i].length; j++) {
                const transformedValue = (Math.max(-25, Math.min(spectrogramData[i][j], 10)) + 25) / 35 * 255;
                ctx.fillStyle = `rgb(${transformedValue}, ${transformedValue}, ${transformedValue})`;
                ctx.fillRect(i - sampleStart, spectrogramData[0].length - j - 1, 1, 1);
            }
        }
        spectroImageCan.value.toBlob((blob) => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sample-${containsAnesthesia ? 'anesthesia' : 'o'}-${containsTickle ? 'tickle' : 'o'}-${Math.floor(Math.random() * 10000)}.png`;
            a.click();
        });
    }
}

async function inference() {
    const numWindows = Math.min(Math.max(1, (frameNumber * 2) / windowSize), spectrogramData.length);
    if (numWindows < 30) return [0, 1, 0]
    const mappedData = [spectrogramData.map((x, i) => {
        return x.map((y) => {
            if (i > (frameNumber * 2) / windowSize) return [0];
            return [(Math.max(-25, Math.min(y, 10)) + 25) / 35];
        });
    }).slice(numWindows - 30, numWindows)];
    console.log(mappedData);
    const output = await model.predict(tf.tensor(mappedData, [1, mappedData[0].length, spectrogramData[0].length, 1]));
    predictions.value = Array.from(output.dataSync())
    console.log(Array.from(predictions.value));
}

function transformSpectrogramDataToTickle(data) {
    rng = seedRandom("" + data[0][0] * data[0][1]);
    const tickleStart = Math.floor(rng() * 90 + 40);
    const tickleEnd = tickleStart + Math.floor(rng() * 30 + 20);
    // decrease 4-12hz activity
    for (let j = tickleStart; j < tickleEnd; j++) {
        for (let i = 4; i <= 12; i++) {
            const binomialProb = Math.sqrt(Math.abs((i - (12 - 4) + 0.5) * 3)) / 4;
            data[j][i] = (data[j][i] + 25) * binomialProb * (rng() + 1) / 2 - 25;
        }
    }
    // increase 13-30hz activity
    for (let j = tickleStart; j < tickleEnd; j++) {
        for (let i = 13; i <= 30; i++) {
            const binomialProb = Math.sqrt(Math.abs(i - (30 - 13) + 0.5)) / 3;
            data[j][i] = (data[j][i] + 25) * (1 / binomialProb) * (rng() + 0.2) / 1.2 - 25;
        }
    }
    return data;
}

function transformSpectrogramDataToAnesthesia(data) {
    rng = seedRandom("" + data[0][0] * data[0][1]);
    const anesthesiaStart = Math.floor(rng() * 30 + 15);
    const anesthesiaEnd = data.length - Math.floor(rng() * 30 + 15);
    // decrease 8-12hz activity
    for (let j = anesthesiaStart; j < anesthesiaEnd; j++) {
        for (let i = 8; i <= 12; i++) {
            const binomialProb = Math.sqrt(Math.abs((i - (12 - 8) + 0.5) * 2)) / 5;
            data[j][i] = (data[j][i] + 25) * binomialProb * (rng() + 1) / 2 - 25;
        }
    }
    // increase 12-30hz activity
    for (let j = anesthesiaEnd; j < data.length; j++) {
        for (let i = 12; i <= 30; i++) {
            const binomialProb = Math.sqrt(Math.abs(i - (30 - 12) + 0.5)) / 3;
            data[j][i] = (data[j][i] + 25) * (1 / binomialProb) * (rng() + 0.2) / 1.2 - 25;
        }
    }
    return data;
}

function computeSpectrogram(data) {
    spectrogramData = [];
    const fft = new FFT(windowSize);
    const input = new Float64Array(windowSize);
    const output = new Float64Array(windowSize * 2); // Output array is twice the length

    for (let windowPos = 0; windowPos <= data.length - windowSize; windowPos += stepSize) {
        const inputData = data.slice(windowPos, windowPos + windowSize);
        for (let i = 0; i < windowSize; i++) {
            input[i] = inputData[i];
        }
        fft.realTransform(output, input);
        const outputArr = Array.from(output);
        let mags = [];
        for (let i = 0; i < outputArr.length; i += 2) {
            mags.push(20 * Math.log10(Math.sqrt(outputArr[i] * outputArr[i] + outputArr[i + 1] * outputArr[i + 1] + 1e-16) / input.length));
        }
        const freqBins = [];
        for (let i = 0; i < windowSize / 2; i++) {
            freqBins.push(i * sampleRate / windowSize);
            if (i * sampleRate / windowSize >= 30) {
                break;
            }
        }
        mags = mags.slice(0, freqBins.length);
        spectrogramData.push(mags);
    }

    spectrogramData = transformSpectrogramDataToTickle(transformSpectrogramDataToAnesthesia(spectrogramData));

    // const graphData = [{
    //     x: data.map((value, i)=>{
    //         return i;
    //     }),
    //     y: data,
    //     type: 'scatter',
    //     mode: 'lines+markers',
    // }];
    // const layout = {
    //     title: 'EEG Spectrogram',
    //     xaxis: {
    //         title: 'Time (minutes)',
    //     },
    //     yaxis: {
    //         title: 'Frequency (Hz)',
    //     },
    // };
    // Plotly.react(plotContainer.value, graphData, layout);
    // const graphData1 = [{
    //     x: freqBins,
    //     y: mags.slice(0, freqBins.length),
    //     type: 'scatter',
    //     mode: 'lines',
    // }];
    // const layout1 = {
    //     title: 'EEG Spectrogram',
    //     xaxis: {
    //         title: 'Frequency (Hz)',
    //     },
    //     yaxis: {
    //         title: 'Power',
    //     },
    // };
    // Plotly.react(plotContainer2.value, graphData1, layout1);

    // for (let start = 0; start <= data.length - windowSize; start += stepSize) {
    //     const windowData = data.slice(start, start + windowSize);

    //     // Copy window data into input array
    //     for (let i = 0; i < windowSize; i++) {
    //         input[i] = windowData[i];
    //     }

    //     // Perform real FFT
    //     fft.realTransform(output, input);
    //     fft.completeSpectrum(output);
    //     const outArr = Array.from(output);
    //     const mags = [];
    //     for (let i = 0; i < outArr.length; i+=2) {
    //         mags.push(10*Math.log10(outArr[i] * outArr[i] + outArr[i+1] * outArr[i+1] + 1e-16));
    //     }

    //     spectrogramData.push(mags);
    // }
};

function plotSpectrogram() {
    if (!plotContainer.value) return;

    // Prepare axes data
    const numWindows = Math.min(Math.max(1, (frameNumber * 2) / windowSize), spectrogramData.length);

    if (numWindows === 0) {
        // Not enough data to compute spectrogram
        return;
    }

    // Time axis in minutes
    const x = [];
    for (let i = 0; i < numWindows; i++) {
        const time = (i * stepSize) / sampleRate / 60; // in minutes
        x.push(time);
    }

    // Frequency axis
    const y = [];
    for (let i = 0; i < windowSize / 2; i++) {
        y.push(i * sampleRate / windowSize);
        if (i * sampleRate / windowSize >= 30) {
            break;
        }
    }

    // Prepare z data (transpose spectrogramData)
    const z = [];
    for (let i = 0; i < y.length; i++) {
        const row = [];
        for (let j = 0; j < numWindows; j++) {
            row.push(spectrogramData[j][i]);
        }
        z.push(row);
    }

    const data = [{
        x: x,
        y: y,
        z: z,
        type: 'heatmap',
        colorscale: 'Jet',
        zmin: -25,
        zmax: 10,
        colorbar: {
            title: 'Power (dB)',
        },
    }];

    const layout = {
        xaxis: {
            title: 'Time (minutes)',
        },
        yaxis: {
            title: 'Frequency (Hz)',
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: {
            family: 'ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
            size: 14,
            color: '#7f7f7f'
        }
    };

    Plotly.react(plotContainer.value, data, layout);
}

watch(
    () => eegData,
    (newData) => {
        if (newData && newData.length >= windowSize) {
            computeSpectrogram(newData);
            plotSpectrogram();
        }
        const numWindows = Math.min(Math.max(1, (frameNumber * 2) / windowSize), spectrogramData.length);
        if (oldNumWindows.value !== numWindows) {
            if (model)
                inference();
            console.log(predictions);
        }
        oldNumWindows.value = numWindows;
    }
);

onMounted(async () => {
    computeSpectrogram(eegData);
    plotSpectrogram();
    model = await loadGraphModel(MODEL_URL);
});
</script>

<style scoped>
/* You can add styles here if needed */
</style>