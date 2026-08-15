// Traffic Light — hardware controller companion sketch (pillar 3).
//
// Mirrors the simulator's four signal heads on 12 LEDs. The app sends one
// line per state change over USB serial at 9600 baud:
//
//     N:G;S:G;E:R;W:R\n      (R=red, A=amber, G=green, O=off)
//
// Wiring — each LED anode through a ~220 ohm resistor to its pin, cathode
// to GND:
//
//     North head: red = 2, amber = 3, green = 4
//     South head: red = 5, amber = 6, green = 7
//     East head:  red = 8, amber = 9, green = 10
//     West head:  red = 11, amber = 12, green = 13

const char HEADS[4] = {'N', 'S', 'E', 'W'};
// [head][0=red, 1=amber, 2=green] -> pin
const int PINS[4][3] = {
    {2, 3, 4},     // N
    {5, 6, 7},     // S
    {8, 9, 10},    // E
    {11, 12, 13},  // W
};

char line[24];  // longest valid line is "N:G;S:G;E:R;W:R" + \n = 17 chars
byte linePos = 0;

void setup() {
    Serial.begin(9600);
    for (int head = 0; head < 4; head++) {
        for (int lamp = 0; lamp < 3; lamp++) {
            pinMode(PINS[head][lamp], OUTPUT);
            digitalWrite(PINS[head][lamp], LOW);
        }
    }
}

void loop() {
    // Non-blocking: drain whatever arrived, apply complete lines only.
    while (Serial.available() > 0) {
        char c = (char)Serial.read();
        if (c == '\n') {
            line[linePos] = '\0';
            applyLine();
            linePos = 0;
        } else if (linePos < sizeof(line) - 1) {
            line[linePos++] = c;
        } else {
            linePos = 0;  // overflow: drop the garbled line, resync on next \n
        }
    }
}

// Parse "N:G;S:G;E:R;W:R" and light the matching lamp on each head.
// Malformed tokens are ignored (head keeps its previous state).
void applyLine() {
    char* token = strtok(line, ";");
    while (token != NULL) {
        if (strlen(token) == 3 && token[1] == ':') {
            applyToken(token[0], token[2]);
        }
        token = strtok(NULL, ";");
    }
}

void applyToken(char head, char letter) {
    for (int i = 0; i < 4; i++) {
        if (HEADS[i] == head) {
            // O (off) leaves every lamp LOW.
            digitalWrite(PINS[i][0], letter == 'R' ? HIGH : LOW);
            digitalWrite(PINS[i][1], letter == 'A' ? HIGH : LOW);
            digitalWrite(PINS[i][2], letter == 'G' ? HIGH : LOW);
            return;
        }
    }
}
