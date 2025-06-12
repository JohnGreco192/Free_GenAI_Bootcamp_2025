
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Activity, Calendar } from "lucide-react";
import { Link, useParams } from "react-router-dom";

const WordDetail = () => {
  const { id } = useParams();
  
  // Mock data - in real app this would come from API
  const word = {
    id: 1,
    word: "Tabarnac",
    translation: "Darn!/Holy!",
    category: "Expressions",
    difficulty: "Common",
    pronunciation: "ta-bar-NAK",
    usage: "Strong expression of surprise or frustration",
    etymology: "Derived from 'tabernacle', a religious term, transformed into a Quebec swear word",
    examples: [
      {
        french: "Tabarnac! J'ai oublié mes clés!",
        english: "Darn! I forgot my keys!"
      },
      {
        french: "Tabarnac que c'est beau!",
        english: "Holy, that's beautiful!"
      }
    ],
    relatedWords: ["Câlice", "Crisse", "Osti"],
    studyHistory: [
      { date: "2024-01-15", activity: "Flashcard Review", score: 85 },
      { date: "2024-01-10", activity: "Usage Practice", score: 92 },
      { date: "2024-01-05", activity: "Pronunciation", score: 78 }
    ]
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      "Expressions": "bg-red-100 text-red-800",
      "Daily Life": "bg-blue-100 text-blue-800"
    };
    return colors[category as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Essential": return "bg-green-100 text-green-800";
      case "Common": return "bg-yellow-100 text-yellow-800";
      case "Cultural": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/words" className="text-blue-600 hover:text-blue-700 text-sm mb-2 block">
            ← Back to Words
          </Link>
          <h1 className="text-4xl font-bold text-blue-700 mb-2">
            {word.word}
          </h1>
          <p className="text-2xl text-gray-700 font-medium">
            {word.translation}
          </p>
          <p className="text-lg text-gray-500 mt-2">
            /{word.pronunciation}/
          </p>
        </div>
        <div className="flex space-x-3">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Activity className="h-4 w-4 mr-2" />
            Practice Word
          </Button>
          <Button variant="outline">
            <BookOpen className="h-4 w-4 mr-2" />
            Edit Word
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Word Details */}
          <Card>
            <CardHeader>
              <CardTitle>Word Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Badge className={getCategoryColor(word.category)}>
                  {word.category}
                </Badge>
                <Badge className={getDifficultyColor(word.difficulty)}>
                  {word.difficulty}
                </Badge>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Usage</h4>
                <p className="text-gray-700">{word.usage}</p>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Etymology</h4>
                <p className="text-gray-700">{word.etymology}</p>
              </div>
            </CardContent>
          </Card>

          {/* Examples */}
          <Card>
            <CardHeader>
              <CardTitle>Examples in Context</CardTitle>
              <CardDescription>See how this word is used in real Quebec French</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {word.examples.map((example, index) => (
                <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <p className="font-medium text-gray-900 mb-2">
                    "{example.french}"
                  </p>
                  <p className="text-gray-600 italic">
                    "{example.english}"
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Related Words */}
          <Card>
            <CardHeader>
              <CardTitle>Related Words</CardTitle>
              <CardDescription>Other Quebec expressions you might find interesting</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {word.relatedWords.map((relatedWord, index) => (
                  <Button key={index} variant="outline" size="sm" asChild>
                    <Link to={`/words/${index + 2}`}>
                      {relatedWord}
                    </Link>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Study Progress */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Calendar className="h-5 w-5" />
                <span>Study Progress</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-4">
                <div className="text-3xl font-bold text-blue-600 mb-1">85%</div>
                <p className="text-sm text-gray-600">Mastery Level</p>
              </div>
              <div className="space-y-3">
                {word.studyHistory.map((session, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <div>
                      <p className="font-medium">{session.activity}</p>
                      <p className="text-gray-500">{session.date}</p>
                    </div>
                    <div className="text-blue-600 font-medium">
                      {session.score}%
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full bg-blue-600 hover:bg-blue-700">
                <Activity className="h-4 w-4 mr-2" />
                Start Flashcard
              </Button>
              <Button variant="outline" className="w-full">
                <BookOpen className="h-4 w-4 mr-2" />
                Add to Group
              </Button>
              <Button variant="outline" className="w-full">
                <Calendar className="h-4 w-4 mr-2" />
                Schedule Review
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default WordDetail;
