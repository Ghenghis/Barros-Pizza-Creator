package tech.daveai.barroscreator;

import android.net.Uri;
import com.google.androidbrowserhelper.trusted.LauncherActivity;

public final class MainActivity extends LauncherActivity {
    @Override
    protected Uri getLaunchingUrl() {
        return Uri.parse(getString(R.string.launch_url));
    }
}
