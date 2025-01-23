#include <WiFi.h>
#include <map>
#include <string>
#include <iostream>
#include <functional>

const char* ssid = "iPhone";
const char* password = "rozrozroz";

enum MessageType {
    MAZE_JUNCTION_END,
    CHECKPOINT_END,
    AUDIO_END,
    UNKNOWN
};

MessageType getMessageType(const std::string& message) {
    static const std::map<std::string, MessageType> messageMap = {
        {"maze_junction_end", MAZE_JUNCTION_END},
        {"checkpoint_end", CHECKPOINT_END},
        {"audio_end", AUDIO_END}
    };

    auto it = messageMap.find(message);
    if (it != messageMap.end()) {
        return it->second;
    }
    return UNKNOWN;
}

void handleMazeJunctionEnd(int data) {
    std::cout << "Handling maze_junction_end\n";
}

void handleCheckpointEnd(int data) {
    std::cout << "Handling checkpoint_end\n";
}

void handleAudioEnd(int data) {
    std::cout << "Handling audio_end\n";
}


std::map<MessageType, std::function<void(int data)>> messageHandlers = {
    {MAZE_JUNCTION_END, handleMazeJunctionEnd},
    {CHECKPOINT_END, handleCheckpointEnd},
    {AUDIO_END, handleAudioEnd}
};

void processMessage(const std::string& message) {

    size_t colonPos = message.find(':');
    if (colonPos == std::string::npos) {
        std::cout << "Invalid message format: " << message << "\n";
        return;
    }

    std::string typeStr = message.substr(0, colonPos);
    int data = std::stoi(message.substr(colonPos + 1));


    MessageType type = getMessageType(typeStr);

    
    if (messageHandlers.find(type) != messageHandlers.end()) {
        messageHandlers[type](data);
    } else {
        std::cout << "Unknown message type: " << typeStr << "\n";
    }
}


void sendMessage(WiFiClient& client, const std::string& message) {
    if (client.connected()) {
        client.print(message.c_str());
        Serial.println("Sent: " + message);
    } else {
        Serial.println("Client not connected. Cannot send message.");
    }
}


void sendCheckpointStart(WiFiClient& client) {
    sendMessage(client, "checkpoint_start");
}

void sendAudioStart(WiFiClient& client) {
    sendMessage(client, "audio_start");
}

void sendMazeJunctionStart(WiFiClient& client) {
    sendMessage(client, "maze_junction_start");
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting...");
  }
  Serial.print("WiFi connected with IP:");
  Serial.println(WiFi.localIP());
}

void loop() {
  WiFiClient client;

  if (!client.connect(IPAddress(172, 20, 10, 9), 10000)) {
    Serial.println("Connection to host failed");
    delay(1000);
    return;
  }

  Serial.println("Connected to server");


  sendCheckpointStart(client);


  if (client.available()) {
    std::string incomingMessage = client.readString().c_str(); // maybe remove this c_str bs
    processMessage(incomingMessage);
  }

  client.stop();
  delay(1000);
}
