import Foundation
import ImageIO
import Vision

struct OcrPayload: Encodable {
    var status: String
    var text: String
    var warnings: [String]
    var engine: String
    var lineCount: Int
}

func emit(_ payload: OcrPayload) -> Never {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys]
    let data = try! encoder.encode(payload)
    FileHandle.standardOutput.write(data)
    exit(0)
}

func fail(_ code: String) -> Never {
    emit(OcrPayload(status: "error", text: "", warnings: [code], engine: "apple_vision", lineCount: 0))
}

let bytes = FileHandle.standardInput.readDataToEndOfFile()
guard !bytes.isEmpty, let source = CGImageSourceCreateWithData(bytes as CFData, nil) else {
    fail("unreadable")
}
guard let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
      let width = properties[kCGImagePropertyPixelWidth] as? Int,
      let height = properties[kCGImagePropertyPixelHeight] as? Int
else {
    fail("unreadable")
}
if width <= 0 || height <= 0 || width > 8000 || height > 8000 || width * height > 12_000_000 {
    fail("too_many_pixels")
}

let thumbnailOptions: [CFString: Any] = [
    kCGImageSourceCreateThumbnailFromImageAlways: true,
    kCGImageSourceCreateThumbnailWithTransform: true,
    kCGImageSourceThumbnailMaxPixelSize: 2400,
]
guard let image = CGImageSourceCreateThumbnailAtIndex(source, 0, thumbnailOptions as CFDictionary) else {
    fail("unreadable")
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["ru-RU", "en-US"]

let handler = VNImageRequestHandler(cgImage: image, options: [:])
do {
    try handler.perform([request])
} catch {
    fail("unreadable")
}

let observations = (request.results ?? []).sorted { left, right in
    let leftY = left.boundingBox.midY
    let rightY = right.boundingBox.midY
    if abs(leftY - rightY) > 0.015 {
        return leftY > rightY
    }
    return left.boundingBox.minX < right.boundingBox.minX
}

var lines: [String] = []
var lowConfidence = false
for observation in observations {
    guard let candidate = observation.topCandidates(1).first else {
        continue
    }
    let line = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
    if line.isEmpty {
        continue
    }
    if candidate.confidence < 0.4 {
        lowConfidence = true
    }
    lines.append(line)
}

if lines.isEmpty {
    emit(OcrPayload(status: "no_text", text: "", warnings: ["no_text"], engine: "apple_vision", lineCount: 0))
}

var warnings: [String] = []
if lowConfidence {
    warnings.append("low_ocr_confidence")
}
emit(
    OcrPayload(
        status: "ok",
        text: lines.joined(separator: "\n"),
        warnings: warnings,
        engine: "apple_vision",
        lineCount: lines.count
    )
)
