// src/pages/Profile.tsx
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  User,
  Building,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Edit3,
  CheckCircle,
  AlertCircle,
  Zap,
  Mic,
  ArrowLeft,
  Camera,
  Shield,
  Settings,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import { doc, getDoc, updateDoc } from "firebase/firestore";
import { db } from "@/firebase";

interface ProfileData {
  firstName: string;
  lastName: string;
  email: string;
  company: string;
  phone?: string;
  location?: string;
  bio?: string;
  avatar?: string;
  verified: boolean;
  accountType: "personal" | "business";
  joinDate: string;
}

const Profile = () => {
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<Partial<ProfileData>>({});
  const navigate = useNavigate();
  const { toast } = useToast();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [formState, setFormState] = useState<Partial<ProfileData>>({});
  const [loading, setLoading] = useState(true);


useEffect(() => {
  const auth = getAuth();
  const unsubscribe = onAuthStateChanged(auth, async (user) => {
    if (user) {
      console.log("✅ Logged in UID:", user.uid);

      const docRef = doc(db, "users", user.uid);
      const docSnap = await getDoc(docRef);

      if (docSnap.exists()) {
        const data = docSnap.data() as ProfileData;
        console.log("✅ Profile data loaded:", data);
        setProfile(data);
        setFormState(data);
      } else {
        console.log("❌ No profile found");
      }

      setLoading(false);
    } else {
      navigate("/login");
    }
  });
  return () => unsubscribe();
}, []);


  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    const auth = getAuth();
    const user = auth.currentUser;
    if (!user || !formData) return;

    try {
      const userRef = doc(db, "users", user.uid);
      await updateDoc(userRef, formData as Partial<ProfileData>);
      setProfileData((prev) => ({ ...prev!, ...formData }));
      setIsEditing(false);
      toast({ title: "Profile updated successfully." });
    } catch (error) {
      toast({ title: "Failed to update profile", variant: "destructive" });
    }
  };

  const calculateProfileCompletion = () => {
    const fields = [
      { key: "firstName", weight: 15 },
      { key: "lastName", weight: 15 },
      { key: "email", weight: 20 },
      { key: "company", weight: 15 },
      { key: "phone", weight: 10 },
      { key: "location", weight: 10 },
      { key: "bio", weight: 10 },
      { key: "avatar", weight: 5 },
    ];

    let completedWeight = 0;

    fields.forEach((field) => {
      if (profileData && profileData[field.key as keyof ProfileData]) {
        completedWeight += field.weight;
      }
    });

    if (profileData?.verified) completedWeight += 10;

    return Math.min(100, Math.round(completedWeight));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (!profileData) return <div className="p-6">Loading...</div>;

  return (
    <div className="min-h-screen bg-background">
      <div className="bg-gradient-hero border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/")}
                className="text-white hover:text-primary"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
              <div className="flex items-center space-x-2">
                <Zap className="h-6 w-6 text-primary" />
                <Mic className="h-4 w-4 text-accent" />
                <span className="text-xl font-bold text-white">Voxaide</span>
              </div>
            </div>
            <Button variant="outline" size="sm" className="border-white/20 text-white hover:bg-white/10">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Profile</h3>
            {!isEditing ? (
              <Button onClick={() => setIsEditing(true)} size="sm">
                <Edit3 className="h-4 w-4 mr-2" /> Edit
              </Button>
            ) : (
              <Button onClick={handleSave} size="sm">
                <CheckCircle className="h-4 w-4 mr-2" /> Save
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {["firstName", "lastName", "email", "company", "phone", "location"].map((key) => (
              <div key={key}>
                <label className="text-sm font-medium text-muted-foreground capitalize">
                  {key}
                </label>
                <input
                  className="w-full mt-1 p-2 border rounded bg-muted/50"
                  name={key}
                  type={key === "email" ? "email" : "text"}
                  disabled={!isEditing || key === "email"}
                  value={(formData as any)[key] || ""}
                  onChange={handleInputChange}
                />
              </div>
            ))}
          </div>

          <div className="mt-4">
            <label className="text-sm font-medium text-muted-foreground">Bio</label>
            <textarea
              className="w-full mt-1 p-2 border rounded bg-muted/50"
              rows={3}
              name="bio"
              disabled={!isEditing}
              value={formData.bio || ""}
              onChange={handleInputChange}
            />
          </div>

          <Separator className="my-4" />

          <div className="flex items-center space-x-2">
            <Badge variant="outline">Account: {profileData.accountType}</Badge>
            <Badge>{profileData.verified ? "Verified" : "Not Verified"}</Badge>
            <Badge variant="secondary">Joined: {formatDate(profileData.joinDate)}</Badge>
          </div>

          <div className="mt-6">
            <span className="text-sm font-medium">Profile Completion</span>
            <Progress value={calculateProfileCompletion()} className="h-2 mt-1" />
            <p className="text-xs text-muted-foreground mt-1">
              {100 - calculateProfileCompletion()}% more to complete your profile
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Profile;
